create or replace procedure ds.fill_account_balance_f(IN i_OnDate date)
language plpgsql
as $$
begin
    insert into logs.etl_log (process_name, status, message)
    values ('ds.fill_account_balance_f', 'start', 'Расчет остатков за дату ' || i_OnDate);

    delete from dm.dm_account_balance_f where on_date = i_OnDate;

    insert into dm.dm_account_balance_f (on_date, account_rk, balance_out, balance_out_rub)
    select
        i_OnDate as on_date,
        acc.account_rk,
        case
            when acc.char_type = 'А' then
                coalesce(prev.balance_out, 0) + coalesce(turn.debet_amount, 0) - coalesce(turn.credit_ammount, 0)
            when acc.char_type = 'П' then
                coalesce(prev.balance_out, 0) - coalesce(turn.debet_amount, 0) + coalesce(turn.credit_ammount, 0)
            else 0
        end as balance_out,
        case
            when acc.char_type = 'А' then
                coalesce(prev.balance_out_rub, 0) + coalesce(turn.debet_amount_rub, 0) - coalesce(turn.credit_amount_rub, 0)
            when acc.char_type = 'П' then
                coalesce(prev.balance_out_rub, 0) - coalesce(turn.debet_amount_rub, 0) + coalesce(turn.credit_amount_rub, 0)
            else 0
        end as balance_out_rub
    from ds.md_account_d acc
    left join dm.dm_account_balance_f prev
        on prev.account_rk = acc.account_rk and prev.on_date = i_OnDate - interval '1 day'
    left join dm.dm_account_turnover_f turn
        on turn.account_rk = acc.account_rk and turn.on_date = i_OnDate
    where i_OnDate between acc.data_actual_date and acc.data_actual_end_date;

    update logs.etl_log
    set status = 'end', end_time = CURRENT_TIMESTAMP, message = 'Расчет остатков завершен за дату ' || i_OnDate
    where process_name = 'ds.fill_account_balance_f' and status = 'start'
      and id = (select id from logs.etl_log where process_name = 'ds.fill_account_balance_f' and status = 'start' order by start_time desc limit 1);
end;
$$;