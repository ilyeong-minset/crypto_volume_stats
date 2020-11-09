create or replace function check_pair_ids(pairs int[])
returns void
language plpgsql
as $$
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

create or replace function align_timestamp(
    ts timestamptz,
    timeframe interval
)
returns timestamptz
language plpgsql
as $$
declare
    seconds int := round(extract(epoch from ts));
    seconds_tf int := round(extract(epoch from timeframe));
begin
    return to_timestamp(seconds - seconds % seconds_tf);
end; $$;

create or replace function aggregate_volume(
    pairs int[],
    ts_from timestamptz,
    timeframe interval,
    cnt int
)
returns table (
    --ts timestamp with time zone,
    ts bigint,
    bought numeric(32, 8),
    sold numeric(32, 8)
)
language plpgsql
as $$
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

create or replace function get_summary(
    pairs int[],
    ts_start timestamptz,
    ts_end timestamptz
)
returns table (
    firstp numeric(32, 8),
    lastp numeric(32, 8),
    lowp numeric(32, 8),
    highp numeric(32, 8),
    avgp numeric(32, 8),
    wavgp numeric(32, 8),
    ntrades int,
    vol numeric(32, 8),
    volup numeric(32, 8),
    voldown numeric(32, 8)
)
language plpgsql
as $$
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

create or replace function get_volume_profile(
    pairs int[],
    ts_start timestamptz,
    ts_end timestamptz,
    frames int
)
returns table (
    low numeric(32, 8),
    high numeric(32, 8),
    bought numeric(32, 8),
    sold numeric(32, 8)
)
language plpgsql
as $$
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

create or replace function get_simple_price_chart(
    pairs int[],
    ts_from timestamptz,
    timeframe interval,
    cnt int
)
returns table (
    --ts timestamptz,
    ts bigint,
    price numeric(32, 8)
)
language plpgsql
as $$
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

create or replace function get_ohlc_chart(
    pairs int[],
    ts_from timestamptz,
    timeframe interval,
    cnt int
)
returns table (
    ts bigint,
    p_open numeric(32, 8),
    p_high numeric(32, 8),
    p_low numeric(32, 8),
    p_close numeric(32, 8)
)
language plpgsql
as $$
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

