create or replace procedure dm.fill_f101_round_f(IN i_OnDate date)
language plpgsql
as $$
declare
    v_from_date date;
    v_to_date date;
    v_balance_in_date date;
begin
    insert into logs.etl_log (process_name, status, message)
    values ('dm.fill_f101_round_f', 'start', 'Расчет 101 формы за дату ' || i_OnDate);

    v_from_date := date_trunc('month', i_OnDate - interval '1 month')::date;
    v_to_date := (date_trunc('month', i_OnDate) - interval '1 day')::date;
    v_balance_in_date := v_from_date - interval '1 day';

    delete from dm.dm_f101_round_f 
    where from_date = v_from_date and to_date = v_to_date;

    insert into dm.dm_f101_round_f (
        from_date, to_date, chapter, ledger_account, characteristic,
        balance_in_rub, balance_in_val, balance_in_total,
        turn_deb_rub, turn_deb_val, turn_deb_total,
        turn_cre_rub, turn_cre_val, turn_cre_total,
        balance_out_rub, balance_out_val, balance_out_total
    )
    select
        v_from_date as from_date,
        v_to_date as to_date,
        las.chapter,
        left(acc.account_number, 5) as ledger_account,
        acc.char_type as characteristic,
        
        coalesce(sum(case 
            when acc.currency_code in ('810', '643') 
            then coalesce(bal_in.balance_out_rub, 0) 
            else 0 
        end), 0) as balance_in_rub,
        
        coalesce(sum(case 
            when acc.currency_code not in ('810', '643') 
            then coalesce(bal_in.balance_out_rub, 0) 
            else 0 
        end), 0) as balance_in_val,
        
        coalesce(sum(coalesce(bal_in.balance_out_rub, 0)), 0) as balance_in_total,
        
        coalesce(sum(case 
            when acc.currency_code in ('810', '643') 
            then coalesce(turn.debet_amount_rub, 0) 
            else 0 
        end), 0) as turn_deb_rub,
        
        coalesce(sum(case 
            when acc.currency_code not in ('810', '643') 
            then coalesce(turn.debet_amount_rub, 0) 
            else 0 
        end), 0) as turn_deb_val,
        
        coalesce(sum(coalesce(turn.debet_amount_rub, 0)), 0) as turn_deb_total,
        
        coalesce(sum(case 
            when acc.currency_code in ('810', '643') 
            then coalesce(turn.credit_amount_rub, 0) 
            else 0 
        end), 0) as turn_cre_rub,
        
        coalesce(sum(case 
            when acc.currency_code not in ('810', '643') 
            then coalesce(turn.credit_amount_rub, 0) 
            else 0 
        end), 0) as turn_cre_val,
        
        coalesce(sum(coalesce(turn.credit_amount_rub, 0)), 0) as turn_cre_total,
        
        coalesce(sum(case 
            when acc.currency_code in ('810', '643') 
            then coalesce(bal_out.balance_out_rub, 0) 
            else 0 
        end), 0) as balance_out_rub,
        
        coalesce(sum(case 
            when acc.currency_code not in ('810', '643') 
            then coalesce(bal_out.balance_out_rub, 0) 
            else 0 
        end), 0) as balance_out_val,
        
        coalesce(sum(coalesce(bal_out.balance_out_rub, 0)), 0) as balance_out_total
        
    from ds.md_account_d acc
    left join ds.md_ledger_account_s las 
        on las.ledger_account = left(acc.account_number, 5)::integer
        and v_from_date between las.start_date and coalesce(las.end_date, '9999-12-31'::date)
    left join dm.dm_account_balance_f bal_in
        on bal_in.account_rk = acc.account_rk 
        and bal_in.on_date = v_balance_in_date
    left join dm.dm_account_balance_f bal_out
        on bal_out.account_rk = acc.account_rk 
        and bal_out.on_date = v_to_date
    left join (
        select 
            account_rk,
            sum(debet_amount_rub) as debet_amount_rub,
            sum(credit_amount_rub) as credit_amount_rub
        from dm.dm_account_turnover_f
        where on_date between v_from_date and v_to_date
        group by account_rk
    ) turn on turn.account_rk = acc.account_rk
    where v_from_date between acc.data_actual_date and acc.data_actual_end_date
    group by las.chapter, left(acc.account_number, 5), acc.char_type
    order by las.chapter, left(acc.account_number, 5);

    update logs.etl_log
    set status = 'end', end_time = CURRENT_TIMESTAMP, 
        message = 'Расчет 101 формы завершен за период с ' || v_from_date || ' по ' || v_to_date
    where process_name = 'dm.fill_f101_round_f' and status = 'start'
      and id = (select id from logs.etl_log 
                where process_name = 'dm.fill_f101_round_f' and status = 'start' 
                order by start_time desc limit 1);
end;
$$; 