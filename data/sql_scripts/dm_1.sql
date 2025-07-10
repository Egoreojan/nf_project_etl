create or replace procedure ds.fill_account_turnover_f(IN i_OnDate date)
language plpgsql
as $$
begin
    insert into logs.etl_log (process_name, status, message)
    values ('ds.fill_account_turnover_f', 'start', 'Расчет витрины оборотов за дату ' || i_OnDate);
    
    delete from dm.dm_account_turnover_f where on_date = i_OnDate;
    
    insert into dm.dm_account_turnover_f (on_date, account_rk, credit_ammount, credit_amount_rub, debet_amount, debet_amount_rub)
    select on_date, account_rk, credit_ammount, credit_amount_rub, debet_amount, debet_amount_rub
    from (
        with credits as (
            select 
                sum(fpf.credit_amount) as credit_amount,
                fpf.credit_account_rk as account_rk
            from ds.ft_posting_f fpf
            where fpf.oper_date = i_OnDate
            group by fpf.credit_account_rk
            ),
            debets as (
                select 
                    sum(fpf.debet_amount) as debet_amount,
                    fpf.debet_account_rk as account_rk
                from ds.ft_posting_f fpf
                where fpf.oper_date = i_OnDate
                group by fpf.debet_account_rk
            )
            select 
                i_OnDate as on_date,
                coalesce(c.account_rk, d.account_rk) as account_rk,
                coalesce(c.credit_amount, 0) as credit_ammount,
                (coalesce(c.credit_amount, 0) * (
                    case 
                        when merd.reduced_cource is null then 1
                        else merd.reduced_cource
                    end)) as credit_amount_rub,
                coalesce(d.debet_amount, 0) as debet_amount,
                (coalesce(d.debet_amount, 0) * (
                    case 
                        when merd.reduced_cource is null then 1
                        else merd.reduced_cource
                    end)) as debet_amount_rub
        from credits c
        full outer join debets d on c.account_rk = d.account_rk
        left join ds.md_account_d mad on coalesce(c.account_rk, d.account_rk) = mad.account_rk
        left join ds.md_exchange_rate_d merd on mad.currency_rk = merd.currency_rk 
            and merd.data_actual_date <= i_OnDate 
            and (merd.data_actual_end_date is null or merd.data_actual_end_date >= i_OnDate)
        order by coalesce(c.account_rk, d.account_rk)
    ) as subquery;
    -- Логируем завершение расчёта
    update logs.etl_log
    set status = 'end', end_time = CURRENT_TIMESTAMP, message = 'Расчет витрины оборотов завершен за дату ' || i_OnDate
    where process_name = 'ds.fill_account_turnover_f' and status = 'start'
      and id = (select id from logs.etl_log where process_name = 'ds.fill_account_turnover_f' and status = 'start' order by start_time desc limit 1);
end;
$$; 