function export_states_csv(filepath, t, x)
%EXPORT_STATES_CSV Columns: time_s, q1_rad, q2_rad, dq1_rad_s, dq2_rad_s.
T = table(t(:), x(:, 1), x(:, 2), x(:, 3), x(:, 4), ...
    'VariableNames', {'time_s', 'q1_rad', 'q2_rad', 'dq1_rad_s', 'dq2_rad_s'});
writetable(T, filepath);
end
