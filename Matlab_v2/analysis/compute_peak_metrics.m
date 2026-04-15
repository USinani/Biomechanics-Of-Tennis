function pm = compute_peak_metrics(t, x, y)
%COMPUTE_PEAK_METRICS Peak timings and values for speeds and joint velocities.
pm = struct();
[speed_max, k_sp] = max(y.speed);
pm.peak_ee_speed = speed_max;
pm.time_peak_ee_speed = t(k_sp);
[d1max, k1] = max(abs(x(:, 3)));
[d2max, k2] = max(abs(x(:, 4)));
pm.peak_shoulder_vel_abs = d1max;
pm.peak_elbow_vel_abs = d2max;
pm.time_peak_shoulder_vel = t(k1);
pm.time_peak_elbow_vel = t(k2);
pm.final_ee_speed = y.speed(end);
end
