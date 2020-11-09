--
-- PostgreSQL database dump
--

-- Dumped from database version 12.4
-- Dumped by pg_dump version 12.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: aggregate_volume(integer[], timestamp with time zone, interval, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.aggregate_volume(pairs integer[], ts_from timestamp with time zone, timeframe interval, cnt integer) RETURNS TABLE(ts bigint, bought numeric, sold numeric)
    LANGUAGE plpgsql
    AS $$
declare
    ts_end timestamptz;
begin
    perform check_pair_ids(pairs);
    for i in 1..cnt loop
        --ts := ts_from;
        ts := round(extract(epoch from ts_from) * 1000);
        ts_end := ts_from + timeframe;
        select
            sum(case when amount > 0 then amount else 0 end),
            abs(sum(case when amount < 0 then amount else 0 end))
        from trades
        where (
            pair = any(pairs)
            and trades.ts >= ts_from
            and trades.ts < ts_end
        )
        into bought, sold;
        return next;
        ts_from := ts_end;
    end loop;
end; $$;


--
-- Name: align_timestamp(timestamp with time zone, interval); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.align_timestamp(ts timestamp with time zone, timeframe interval) RETURNS timestamp with time zone
    LANGUAGE plpgsql
    AS $$
declare
    seconds int := round(extract(epoch from ts));
    seconds_tf int := round(extract(epoch from timeframe));
begin
    return to_timestamp(seconds - seconds % seconds_tf);
end; $$;


--
-- Name: check_pair_ids(integer[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.check_pair_ids(pairs integer[]) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    p int;
begin
    foreach p in array pairs
    loop
        if not exists (select 1 from pairs where pairs.id = p)
        then
            raise exception 'Nonexistent pair ID: %', p;
        end if;
    end loop;
end; $$;


--
-- Name: get_ohlc_chart(integer[], timestamp with time zone, interval, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_ohlc_chart(pairs integer[], ts_from timestamp with time zone, timeframe interval, cnt integer) RETURNS TABLE(ts bigint, p_open numeric, p_high numeric, p_low numeric, p_close numeric)
    LANGUAGE plpgsql
    AS $$
declare
    ts_end timestamptz;
begin
    perform check_pair_ids(pairs);
    ts_from := align_timestamp(ts_from, timeframe);
    for i in 1..cnt loop
        ts_end := ts_from + timeframe;
        --ts := ts_from;
        ts := round(extract(epoch from ts_from) * 1000);
        with result as (
            select * from trades
            where (
                pair = any(pairs)
                and trades.ts >= ts_from
                and trades.ts < ts_end
            )
        ) select
            (select price from result order by result.ts asc limit 1),
            max(price),
            min(price),
            (select price from result order by result.ts desc limit 1)--,
            --sum(case when amount > 0 then amount else 0 end),
            --abs(sum(case when amount < 0 then amount else 0 end))
        from result
        into p_open, p_high, p_low, p_close;--, vol_up, vol_down;
        return next;
        ts_from := ts_end;
    end loop;
end; $$;


--
-- Name: get_simple_price_chart(integer[], timestamp with time zone, interval, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_simple_price_chart(pairs integer[], ts_from timestamp with time zone, timeframe interval, cnt integer) RETURNS TABLE(ts bigint, price numeric)
    LANGUAGE plpgsql
    AS $$
declare
    ts_end timestamptz;
    next_price numeric(32, 8);
    ts_now timestamptz := now();
begin
    perform check_pair_ids(pairs);
    for i in 1..cnt loop
        --ts := ts_from;
        ts := round(extract(epoch from ts_from) * 1000);
        ts_end := ts_from + timeframe;
        with result as (
            select * from trades
            where (
                pair = any(pairs)
                and trades.ts >= ts_from
                and trades.ts < ts_end
            )
        ) select
            (select result.price from result order by result.ts asc limit 1),
            avg(result.price)
        from result
        into price, next_price;
        return next;
        price := next_price;
        ts := ts_from + timeframe / 2;
        return next;
        ts_from := ts_end;
    end loop;
    -- ts := ts_end;
    -- ts_from := ts_end - timeframe / 2;
    -- select trades.price from trades
    -- where (
        -- pair = any(pairs)
        -- and trades.ts >= ts_from
        -- and trades.ts < ts_end
    -- )
    -- order by trades.ts desc limit 1
    -- into price;
    -- return next;
end; $$;


--
-- Name: get_summary(integer[], timestamp with time zone, timestamp with time zone); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_summary(pairs integer[], ts_start timestamp with time zone, ts_end timestamp with time zone) RETURNS TABLE(firstp numeric, lastp numeric, lowp numeric, highp numeric, avgp numeric, wavgp numeric, ntrades integer, vol numeric, volup numeric, voldown numeric)
    LANGUAGE plpgsql
    AS $$
begin
    perform check_pair_ids(pairs);
    with result as (
        select * from trades
        where (
            pair = any(pairs)
            and trades.ts >= ts_start
            and trades.ts < ts_end
        )
    ) select
        (select price from result order by ts limit 1),
        (select price from result order by ts desc limit 1),
        min(price),
        max(price),
        avg(price),
        sum(price * amount) / sum(amount),
        count(*),
        sum(abs(amount)) as vol,
        sum(
            case when amount > 0
            then amount
            else 0 end
        ),
        abs(sum(
            case when amount < 0
            then amount
            else 0 end
        ))
    from result
    into firstp, lastp, lowp, highp, avgp, wavgp, ntrades, vol, volup, voldown;
    return next;
end; $$;


--
-- Name: get_volume_profile(integer[], timestamp with time zone, timestamp with time zone, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_volume_profile(pairs integer[], ts_start timestamp with time zone, ts_end timestamp with time zone, frames integer) RETURNS TABLE(low numeric, high numeric, bought numeric, sold numeric)
    LANGUAGE plpgsql
    AS $$
declare
    minp numeric(32, 8);
    maxp numeric(32, 8);
    step numeric(32, 8);
begin
    perform check_pair_ids(pairs);
    create temporary table tmp_trades
        on commit drop
        as (
            select price, amount from trades
            where (
                pair = any(pairs) and
                ts >= ts_start and
                ts < ts_end
            )
        );
    select min(price), max(price) from tmp_trades into minp, maxp;
    step := (maxp - minp) / frames;
    while maxp > minp loop
        high := maxp;
        low := high - step;
        select
            sum(case when amount > 0 then amount else 0 end),
            abs(sum(case when amount < 0 then amount else 0 end))
        from tmp_trades
        where (price >= low and price < high)
        into bought, sold;
        maxp := low;
        return next;
    end loop;
end; $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: exchanges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.exchanges (
    id integer NOT NULL,
    name character varying NOT NULL,
    display_name character varying
);


--
-- Name: exchanges_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.exchanges_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: exchanges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.exchanges_id_seq OWNED BY public.exchanges.id;


--
-- Name: pairs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pairs (
    id integer NOT NULL,
    exchange integer NOT NULL,
    base character varying NOT NULL,
    quote character varying NOT NULL
);


--
-- Name: pairs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pairs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pairs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pairs_id_seq OWNED BY public.pairs.id;


--
-- Name: trades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trades (
    id integer NOT NULL,
    pair integer NOT NULL,
    ts timestamp with time zone NOT NULL,
    amount numeric(32,8) NOT NULL,
    price numeric(32,8) NOT NULL
);


--
-- Name: trades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trades_id_seq OWNED BY public.trades.id;


--
-- Name: exchanges id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchanges ALTER COLUMN id SET DEFAULT nextval('public.exchanges_id_seq'::regclass);


--
-- Name: pairs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pairs ALTER COLUMN id SET DEFAULT nextval('public.pairs_id_seq'::regclass);


--
-- Name: trades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trades ALTER COLUMN id SET DEFAULT nextval('public.trades_id_seq'::regclass);


--
-- Name: exchanges exchanges_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchanges
    ADD CONSTRAINT exchanges_name_key UNIQUE (name);


--
-- Name: exchanges exchanges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchanges
    ADD CONSTRAINT exchanges_pkey PRIMARY KEY (id);


--
-- Name: pairs pairs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pairs
    ADD CONSTRAINT pairs_pkey PRIMARY KEY (id);


--
-- Name: trades trades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_pkey PRIMARY KEY (id);


--
-- Name: trades_idx_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX trades_idx_ts ON public.trades USING btree (pair, ts);


--
-- Name: pairs pairs_exchange_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pairs
    ADD CONSTRAINT pairs_exchange_fkey FOREIGN KEY (exchange) REFERENCES public.exchanges(id);


--
-- Name: trades trades_pair_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_pair_fkey FOREIGN KEY (pair) REFERENCES public.pairs(id);


--
-- PostgreSQL database dump complete
--

