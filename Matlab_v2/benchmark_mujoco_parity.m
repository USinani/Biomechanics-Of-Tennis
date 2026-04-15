function summary = benchmark_mujoco_parity(varargin)
%BENCHMARK_MUJOCO_PARITY Compare MATLAB run_swing_sim to systematic_studies CSV.
% benchmark_mujoco_parity() uses default repo-relative CSV path.
% Optional: benchmark_mujoco_parity('csv_path', '/path/to.csv', 'tau_amp', 5, ...)

p = inputParser;
addParameter(p, 'csv_path', '', @ischar);
addParameter(p, 'q1_deg', 5, @isnumeric);
addParameter(p, 'q2_deg', 55, @isnumeric);
addParameter(p, 'tau_amp', [], @isnumeric);
addParameter(p, 'tau_f_hz', 0.8, @isnumeric);
addParameter(p, 'tau_phase_deg', 30, @isnumeric);
addParameter(p, 'strict_assert', true, @islogical);
parse(p, varargin{:});

here = fileparts(mfilename('fullpath'));
addpath(genpath(here));

csv_path = char(p.Results.csv_path);
if isempty(csv_path)
    matlab_v2 = fileparts(mfilename('fullpath'));
    repo = fileparts(matlab_v2);
    csv_path = fullfile(repo, 'systematic_studies', 'outputs', 'swing_benchmark_timeseries.csv');
end
if exist(csv_path, 'file') ~= 2
    error('benchmark_mujoco_parity:file', ...
        ['CSV not found: %s\nGenerate with: ' ...
        'python systematic_studies/swing_benchmark_mujoco_vs_bridge.py'], csv_path);
end

T = readtable(csv_path);
t_csv = T.time_s;
if numel(t_csv) < 3
    error('benchmark_mujoco_parity:time', 'CSV must contain at least 3 time samples.');
end
dt_vec = diff(t_csv);
if any(dt_vec <= 0)
    error('benchmark_mujoco_parity:time', 'Time column must be strictly increasing.');
end
dt = median(dt_vec);
if p.Results.strict_assert && any(abs(dt_vec - dt) > max(1e-10, 1e-6 * dt))
    error('benchmark_mujoco_parity:time', 'Non-uniform dt in CSV; cannot enforce parity.');
end

tau1_csv = get_col(T, {'tau1_Nm', 'tau0'});
tau2_csv = get_col(T, {'tau2_Nm', 'tau1'});

params = default_params();
params.dt = dt;
params.t_end = t_csv(end);
params.q0 = [deg2rad(p.Results.q1_deg); deg2rad(p.Results.q2_deg)];
params.qd0 = [0; 0];
params.control.type = 'piecewise';
params.control.piecewise_times = t_csv;
params.control.piecewise_taus = [tau1_csv, tau2_csv];
params.control.tau_amp = 0.0;
params.control.tau_f_hz = p.Results.tau_f_hz;
params.control.tau_phase_deg = p.Results.tau_phase_deg;

[t_m, x_m, ~, y_m, ~] = run_swing_sim(params);

q_m = interp1(t_m, x_m(:, 1:2), t_csv, 'linear', 'extrap');
qd_m = interp1(t_m, x_m(:, 3:4), t_csv, 'linear', 'extrap');
sp_m = interp1(t_m, y_m.speed, t_csv, 'linear', 'extrap');

summary = struct();
q_bridge = [];
qd_bridge = [];
if all(ismember({'bridge_q1_rad','bridge_q2_rad'}, T.Properties.VariableNames))
    q_bridge = [T.bridge_q1_rad, T.bridge_q2_rad];
elseif all(ismember({'bridge_q1','bridge_q2'}, T.Properties.VariableNames))
    q_bridge = [T.bridge_q1, T.bridge_q2];
end
if all(ismember({'bridge_qdot1_rad_s','bridge_qdot2_rad_s'}, T.Properties.VariableNames))
    qd_bridge = [T.bridge_qdot1_rad_s, T.bridge_qdot2_rad_s];
elseif all(ismember({'bridge_qd1','bridge_qd2'}, T.Properties.VariableNames))
    qd_bridge = [T.bridge_qd1, T.bridge_qd2];
end
if ~isempty(q_bridge)
    q_b = q_bridge;
    if isempty(qd_bridge)
        error('benchmark_mujoco_parity:bridge', 'Bridge qdot columns missing while q columns are present.');
    end
    summary.rmse_q_matlab_vs_bridge = sqrt(mean(sum((q_m - q_b).^2, 2)));
    summary.rmse_qd_matlab_vs_bridge = sqrt(mean(sum((qd_m - qd_bridge).^2, 2)));
    bridge_speed = get_col(T, {'bridge_ee_speed_xz_m_s', 'bridge_hand_speed_xz'});
    summary.rmse_hand_speed_matlab_vs_bridge = sqrt(mean((sp_m - bridge_speed).^2));
end
q_mj = [];
if all(ismember({'mujoco_q1_rad','mujoco_q2_rad'}, T.Properties.VariableNames))
    q_mj = [T.mujoco_q1_rad, T.mujoco_q2_rad];
elseif all(ismember({'mj_q1_deg','mj_q2_deg'}, T.Properties.VariableNames))
    q_mj = deg2rad([T.mj_q1_deg, T.mj_q2_deg]);
end
if ~isempty(q_mj)
    mj_q = q_mj;
    mj_qd = [get_col(T, {'mujoco_qdot1_rad_s', 'mj_qd1_rad_s'}), ...
             get_col(T, {'mujoco_qdot2_rad_s', 'mj_qd2_rad_s'})];
    mj_speed = get_col(T, {'mujoco_ee_speed_fd_xz_m_s', 'mj_hand_speed_norm_fd'});
    summary.rmse_q_matlab_vs_mj = sqrt(mean(sum((q_m - mj_q).^2, 2)));
    summary.rmse_qd_matlab_vs_mj = sqrt(mean(sum((qd_m - mj_qd).^2, 2)));
    summary.rmse_hand_speed_matlab_vs_mj = sqrt(mean((sp_m - mj_speed).^2));
end

[~, im] = max(y_m.speed);
if any(ismember({'bridge_ee_speed_xz_m_s', 'bridge_hand_speed_xz'}, T.Properties.VariableNames))
    bridge_speed = get_col(T, {'bridge_ee_speed_xz_m_s', 'bridge_hand_speed_xz'});
    [~, ib] = max(bridge_speed);
    summary.peak_speed_diff_bridge = max(y_m.speed) - max(bridge_speed);
    summary.peak_time_diff_s_bridge = t_m(im) - t_csv(ib);
end

u_expected = [tau1_csv, tau2_csv];
u_replayed = interp1(t_m, control_matrix_from_params(t_m, params), t_csv, 'previous', 'extrap');
torque_abs_err = abs(u_replayed - u_expected);
summary.torque_profile_rmse_nm = sqrt(mean(sum((u_replayed - u_expected).^2, 2)));
summary.torque_profile_max_abs_err_nm = max(torque_abs_err(:));
if p.Results.strict_assert && summary.torque_profile_max_abs_err_nm > 1e-9
    error('benchmark_mujoco_parity:torque', ...
        'Torque profile mismatch between CSV and MATLAB replay (max abs err=%g).', ...
        summary.torque_profile_max_abs_err_nm);
end

summary.csv_path = csv_path;
summary.matlab_dt = params.dt;
summary.matlab_t_end = params.t_end;
summary.csv_duration = t_csv(end);
summary.csv_dt = dt;
summary.contract_fields = {'time_s','matlab_q1_rad','matlab_q2_rad','matlab_qdot1_rad_s','matlab_qdot2_rad_s', ...
    'mujoco_q1_rad','mujoco_q2_rad','mujoco_qdot1_rad_s','mujoco_qdot2_rad_s','tau1_Nm','tau2_Nm'};

if p.Results.strict_assert && abs(summary.matlab_dt - summary.csv_dt) > 1e-12
    error('benchmark_mujoco_parity:dt', 'MATLAB dt does not match CSV dt.');
end
if p.Results.strict_assert && abs(summary.matlab_t_end - summary.csv_duration) > max(1e-9, summary.csv_dt)
    error('benchmark_mujoco_parity:duration', 'MATLAB horizon does not match CSV duration.');
end

out_root = fullfile(fileparts(mfilename('fullpath')), 'outputs', 'mujoco_benchmark');
rid = build_run_id('parity');
out_dir = fullfile(out_root, rid);
ensure_dir(out_dir);

fid = fopen(fullfile(out_dir, 'parity_summary.json'), 'w');
fprintf(fid, '%s', jsonencode(summary));
fclose(fid);
save(fullfile(out_dir, 'parity_summary.mat'), 'summary', 't_csv', 't_m', 'x_m', 'y_m', 'q_m', 'sp_m', 'T', '-v7');

parity_tbl = table();
parity_tbl.time_s = t_csv;
parity_tbl.matlab_q1_rad = q_m(:, 1);
parity_tbl.matlab_q2_rad = q_m(:, 2);
parity_tbl.matlab_qdot1_rad_s = qd_m(:, 1);
parity_tbl.matlab_qdot2_rad_s = qd_m(:, 2);
parity_tbl.matlab_ee_speed_m_s = sp_m;
if ~isempty(q_mj)
    parity_tbl.mujoco_q1_rad = q_mj(:, 1);
    parity_tbl.mujoco_q2_rad = q_mj(:, 2);
    parity_tbl.mujoco_qdot1_rad_s = mj_qd(:, 1);
    parity_tbl.mujoco_qdot2_rad_s = mj_qd(:, 2);
end
if any(ismember({'mujoco_ee_speed_fd_xz_m_s', 'mj_hand_speed_norm_fd'}, T.Properties.VariableNames))
    parity_tbl.mujoco_ee_speed_fd_xz_m_s = get_col(T, {'mujoco_ee_speed_fd_xz_m_s', 'mj_hand_speed_norm_fd'});
end
if ismember('mujoco_ee_speed_jac_xz_m_s', T.Properties.VariableNames)
    parity_tbl.mujoco_ee_speed_jac_xz_m_s = T.mujoco_ee_speed_jac_xz_m_s;
end
if ~isempty(q_bridge)
    parity_tbl.bridge_q1_rad = q_bridge(:, 1);
    parity_tbl.bridge_q2_rad = q_bridge(:, 2);
    parity_tbl.bridge_qdot1_rad_s = qd_bridge(:, 1);
    parity_tbl.bridge_qdot2_rad_s = qd_bridge(:, 2);
    parity_tbl.bridge_ee_speed_xz_m_s = get_col(T, {'bridge_ee_speed_xz_m_s', 'bridge_hand_speed_xz'});
end
parity_tbl.tau1_Nm = tau1_csv;
parity_tbl.tau2_Nm = tau2_csv;
writetable(parity_tbl, fullfile(out_dir, 'parity_timeseries.csv'));

fh = figure('Visible', 'off');
subplot(2, 1, 1);
hold on;
plot(t_csv, q_m(:, 1), 'b-', 'DisplayName', 'MATLAB q1');
plot(t_csv, q_m(:, 2), 'r-', 'DisplayName', 'MATLAB q2');
if ~isempty(q_bridge)
    plot(t_csv, q_bridge(:, 1), 'b--', 'DisplayName', 'bridge q1');
    plot(t_csv, q_bridge(:, 2), 'r--', 'DisplayName', 'bridge q2');
end
xlabel('Time (s)');
ylabel('q (rad)');
title('Joint angles: MATLAB vs CSV bridge');
legend('Location', 'best');
grid on;
subplot(2, 1, 2);
hold on;
plot(t_m, y_m.speed, 'k-', 'DisplayName', 'MATLAB EE speed');
if ~isempty(q_bridge)
    plot(t_csv, get_col(T, {'bridge_ee_speed_xz_m_s', 'bridge_hand_speed_xz'}), 'k--', 'DisplayName', 'bridge hand speed');
end
if any(ismember({'mujoco_ee_speed_fd_xz_m_s', 'mj_hand_speed_norm_fd'}, T.Properties.VariableNames))
    plot(t_csv, get_col(T, {'mujoco_ee_speed_fd_xz_m_s', 'mj_hand_speed_norm_fd'}), 'm:', 'DisplayName', 'MuJoCo hand speed');
end
xlabel('Time (s)');
ylabel('Speed (m/s)');
title('Hand / EE speed');
legend('Location', 'best');
grid on;
saveas(fh, fullfile(out_dir, 'parity_overlay.png'));
close(fh);

disp(summary);
fprintf('Wrote %s\n', fullfile(out_dir, 'parity_summary.json'));
end

function out = get_col(T, candidates)
for i = 1:numel(candidates)
    name = candidates{i};
    if ismember(name, T.Properties.VariableNames)
        out = T.(name);
        return;
    end
end
error('benchmark_mujoco_parity:column', 'Missing required column. Tried: %s', strjoin(candidates, ', '));
end

function u = control_matrix_from_params(t, params)
u = zeros(numel(t), 2);
for k = 1:numel(t)
    uk = control_profile(t(k), params);
    u(k, :) = uk(:)';
end
end
