function export_controls_csv(filepath, t, u_hist)
%EXPORT_CONTROLS_CSV Columns: time_s, tau_shoulder_nm, tau_elbow_nm.
T = table(t(:), u_hist(:, 1), u_hist(:, 2), ...
    'VariableNames', {'time_s', 'tau_shoulder_nm', 'tau_elbow_nm'});
writetable(T, filepath);
end
