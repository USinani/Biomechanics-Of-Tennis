function cmp = compare_trajectories(t_a, x_a, y_a, t_b, x_b, y_b, label_a, label_b)
%COMPARE_TRAJECTORIES RMSE and peak deltas between two runs (resample b onto t_a).
if nargin < 7
    label_a = 'A';
end
if nargin < 8
    label_b = 'B';
end
q_a = x_a(:, 1:2);
qd_a = x_a(:, 3:4);
q_b = interp1(t_b, x_b(:, 1:2), t_a, 'linear', 'extrap');
qd_b = interp1(t_b, x_b(:, 3:4), t_a, 'linear', 'extrap');
sp_b = interp1(t_b, y_b.speed, t_a, 'linear', 'extrap');
cmp = struct();
cmp.rmse_q = sqrt(mean(sum((q_a - q_b).^2, 2)));
cmp.rmse_qd = sqrt(mean(sum((qd_a - qd_b).^2, 2)));
cmp.rmse_ee_speed = sqrt(mean((y_a.speed - sp_b).^2));
[mx_a, ia] = max(y_a.speed);
[mx_b, ib] = max(y_b.speed);
cmp.peak_speed_diff = mx_a - mx_b;
cmp.peak_time_diff_s = t_a(ia) - t_b(ib);
cmp.final_state_q_err = norm(x_a(end, 1:2) - x_b(end, 1:2));
cmp.final_state_qd_err = norm(x_a(end, 3:4) - x_b(end, 3:4));
cmp.label_a = label_a;
cmp.label_b = label_b;
end
