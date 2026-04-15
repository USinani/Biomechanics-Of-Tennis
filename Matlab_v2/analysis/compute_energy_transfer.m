function et = compute_energy_transfer(t, x, u_hist, y, params)
%COMPUTE_ENERGY_TRANSFER Segment KE, joint power/work, simple coordination proxy.
N = numel(t);
dt = mean(diff(t));
if isempty(dt) || ~isfinite(dt)
    dt = params.dt;
end
qd = x(:, 3:4);
power = sum(u_hist .* qd, 2);
work_cum = cumtrapz(t, power);
d1 = qd(:, 1);
d2 = qd(:, 2);
[~, i1] = max(abs(d1));
[~, i2] = max(abs(d2));
timing_lag_s = t(i2) - t(i1);
et = struct();
et.ke_link1 = y.ke1;
et.ke_link2 = y.ke2;
et.pe = y.pe;
et.joint_power = power;
et.joint_work_cum = work_cum;
et.total_work = work_cum(end);
et.timing_lag_peak_abs_vel_s = timing_lag_s;
et.duration_s = t(end) - t(1);
et.N = N;
end
