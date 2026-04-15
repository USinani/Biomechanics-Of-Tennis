function metrics = compute_metrics(t, x, u_hist, y, params)
%COMPUTE_METRICS Summary metrics for a swing run (publication / MuJoCo comparison).
pm = compute_peak_metrics(t, x, y);
if isfield(y, 'energy_transfer')
    et = y.energy_transfer;
else
    et = compute_energy_transfer(t, x, u_hist, y, params);
end
metrics = struct();
metrics.peak_ee_speed = pm.peak_ee_speed;
metrics.time_peak_ee_speed = pm.time_peak_ee_speed;
metrics.peak_shoulder_angular_vel = pm.peak_shoulder_vel_abs;
metrics.peak_elbow_angular_vel = pm.peak_elbow_vel_abs;
metrics.final_ee_speed = pm.final_ee_speed;
metrics.total_mechanical_energy = y.energy_total;
metrics.energy_final = y.energy_total(end);
metrics.energy_initial = y.energy_total(1);
if metrics.energy_initial ~= 0
    metrics.energy_transfer_efficiency_proxy = (pm.peak_ee_speed^2) / max(abs(metrics.energy_initial), eps);
else
    metrics.energy_transfer_efficiency_proxy = pm.peak_ee_speed^2;
end
metrics.joint_work_total = et.total_work;
metrics.timing_lag_proximal_distal_peak_vel_s = et.timing_lag_peak_abs_vel_s;
metrics.trajectory_duration_s = t(end) - t(1);
metrics.timing_peak_shoulder_vel_s = pm.time_peak_shoulder_vel;
metrics.timing_peak_elbow_vel_s = pm.time_peak_elbow_vel;
end
