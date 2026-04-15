function paths = generate_plots(t, x, u_hist, y, out_dir, prefix)
%GENERATE_PLOTS Standard time-series figures (PNG; FIG if supported).
if nargin < 6
    prefix = 'fig';
end
ensure_dir(out_dir);
paths = struct('png', {{}}, 'fig', {{}});
base = fullfile(out_dir, prefix);

fh = figure('Visible', 'off');
plot(t, x(:, 1:2));
xlabel('Time (s)');
ylabel('Angle (rad)');
title('Joint angles');
legend('q1 shoulder', 'q2 elbow', 'Location', 'best');
grid on;
paths = save_one(paths, fh, [base '_joint_angles']);

fh = figure('Visible', 'off');
plot(t, x(:, 3:4));
xlabel('Time (s)');
ylabel('Angular velocity (rad/s)');
title('Joint velocities');
legend('dq1', 'dq2', 'Location', 'best');
grid on;
paths = save_one(paths, fh, [base '_joint_vel']);

fh = figure('Visible', 'off');
plot(t, u_hist);
xlabel('Time (s)');
ylabel('Torque (N·m)');
title('Joint torques');
legend('shoulder', 'elbow', 'Location', 'best');
grid on;
paths = save_one(paths, fh, [base '_torques']);

fh = figure('Visible', 'off');
plot(t, y.speed);
xlabel('Time (s)');
ylabel('Speed (m/s)');
title('End-effector speed');
grid on;
paths = save_one(paths, fh, [base '_ee_speed']);

fh = figure('Visible', 'off');
plot(t, y.energy_total);
xlabel('Time (s)');
ylabel('Energy (J)');
title('Total mechanical energy (proxy)');
grid on;
paths = save_one(paths, fh, [base '_energy']);
end

function paths = save_one(paths, fh, base)
pngp = [base '.png'];
saveas(fh, pngp);
paths.png{end + 1} = pngp;
try
    savefig(fh, [base '.fig']);
    paths.fig{end + 1} = [base '.fig'];
catch
end
close(fh);
end
