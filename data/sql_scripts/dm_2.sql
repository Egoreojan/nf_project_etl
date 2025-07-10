create or replace procedure dm.fill_account_balance_f(IN i_OnDate date)
language plpgsql
as $$
begin
    insert into logs.etl_log (process_name, status, message)
    values ('dm.fill_account_balance_f', 'start', 'Наполнение витрины fill_account_balance_f за дату: ' || i_OnDate);

    delete from dm.dm_account_balance_f where on_date = i_OnDate;

    insert into dm.dm_account_balance_f (on_date, account_rk, balance_out, balance_out_rub)
    select
        fb.on_date,
        fb.account_rk,
        fb.balance_out,
        fb.balance_out * COALESCE(merd.reduced_cource, 1) AS balance_out_rub
    from ds.ft_balance_f fb
    left join ds.md_account_d mad on fb.account_rk = mad.account_rk
    left join ds.md_exchange_rate_d merd
        on mad.currency_rk = merd.currency_rk
        and merd.data_actual_date <= i_OnDate
        and (merd.data_actual_end_date IS NULL OR merd.data_actual_end_date >= i_OnDate)
    where fb.on_date = i_OnDate;

    update logs.etl_log
    set status = 'end', end_time = CURRENT_TIMESTAMP, message = 'Наполнение витрины fill_account_balance_f завершен за дату ' || i_OnDate
    where process_name = 'dm.fill_account_balance_f' and status = 'start'
      and id = (select id from logs.etl_log where process_name = 'dm.fill_account_balance_f' and status = 'start' order by start_time desc limit 1);
end;
$$;