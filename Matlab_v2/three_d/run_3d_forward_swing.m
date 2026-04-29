function results = run_3d_forward_swing(varargin)
%RUN_3D_FORWARD_SWING Top-level kinematic forehand swing -> ball impact -> Unity export.
%
% Phase 0 driver that wires together the existing Matlab_v2/three_d scaffold:
%   default_params_3d -> min_jerk_swing -> fk_5dof_arm -> ball_dynamics_3d ->
%   ball_racket_collision -> export_unity_swing_csv / _jsonl -> stream_swing_udp.
%
% Default DOF mode is "two_link_planar" (only shoulder pitch q1 + elbow
% flexion q3 move; q2 yaw, q4 pronation, q5 wrist locked at 0). This keeps
% the 3D demo aligned with the rest of the PhD project (example_two_link/
% two_link_arm.xml is a 2-DOF arm). The full 5-DOF code path stays live
% behind 'dof_mode','five_dof_full'.
%
% Outputs:
%   <output_root>/<experiment_name>/<run_id>/
%       states.csv     - per-Unity-frame, 41 columns, RHS Z-up
%       states.jsonl   - same payload, one JSON object per line
%       schema.json    - schema metadata + run-level summary (peak speed,
%                        contact velocity, post-impact ball velocity)
%       swing_3d.png   - 4-panel summary figure (if 'plot', true)
%
% Name-Value options:
%   'dof_mode'        char    'two_link_planar' (default) | 'five_dof_full'
%   'stream'          logical false (default). If true, push the JSONL over
%                             UDP after writing, using params.streaming.*
%   'plot'            logical true  (default). Render plot_swing_3d.
%   'keyframes_csv'   char    Optional 5x(M+1) CSV of joint keyframes (deg)
%                             that overrides params.swing.q_keyframes_deg.
%   'experiment_name' char    Override params.export.experiment_name.
%
% Usage:
%   results = run_3d_forward_swing();                              % default
%   results = run_3d_forward_swing('dof_mode','five_dof_full');    % full 5-DOF
%   results = run_3d_forward_swing('stream',true);                 % + UDP
%
% Returns:
%   results.params           full params struct used
%   results.frames           Unity-rate per-frame struct
%   results.ball_pre         Nx6 [pos, vel] before impact (sim rate)
%   results.ball_post        Mx6 [pos, vel] after impact  (sim rate)
%   results.contact          struct (t_s, racket_speed_mps, face_normal,
%                            ball_v_pre, ball_v_post, ball_spin_post)
%   results.out_dir          output folder
%   results.csv / .jsonl / .schema   absolute paths

% --------- arg parsing ----------------------------------------------------
p = inputParser;
p.FunctionName = 'run_3d_forward_swing';
p.addParameter('dof_mode', 'two_link_planar', @(s) ischar(s) || isstring(s));
p.addParameter('stream', false, @(x) islogical(x) || (isnumeric(x) && isscalar(x)));
p.addParameter('plot', true,   @(x) islogical(x) || (isnumeric(x) && isscalar(x)));
p.addParameter('keyframes_csv', '', @(s) ischar(s) || isstring(s));
p.addParameter('experiment_name', '', @(s) ischar(s) || isstring(s));
p.parse(varargin{:});
opts = p.Results;
opts.dof_mode = char(opts.dof_mode);

% --------- path setup -----------------------------------------------------
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, 'kinematics'));
addpath(fullfile(here, 'trajectories'));
addpath(fullfile(here, 'ball'));
addpath(fullfile(here, 'export'));
addpath(fullfile(here, 'streaming'));
addpath(fullfile(fileparts(here), 'utils'));

% --------- params + dof mode ---------------------------------------------
params = default_params_3d();
if ~isempty(opts.experiment_name)
    params.export.experiment_name = char(opts.experiment_name);
end
if isempty(params.export.run_id)
    params.export.run_id = build_run_id(params.export.experiment_name);
end

switch lower(opts.dof_mode)
    case 'two_link_planar'
        % Lock q2 (sh-yaw), q4 (pronation), q5 (wrist) at 0 across all
        % keyframes. q1 (sh-pitch) and q3 (elbow flexion) drive the swing.
        params.swing.q_keyframes_deg([2 4 5], :) = 0;
        params.dof_mode = 'two_link_planar';
    case 'five_dof_full'
        params.dof_mode = 'five_dof_full';
    otherwise
        error('run_3d_forward_swing:dof_mode', ...
            'Unknown dof_mode "%s" (use two_link_planar | five_dof_full).', ...
            opts.dof_mode);
end

% --------- optional motion-capture-style keyframes -----------------------
if ~isempty(opts.keyframes_csv)
    kf_path = char(opts.keyframes_csv);
    if ~isfile(kf_path)
        error('run_3d_forward_swing:keyframes_csv', ...
            'keyframes_csv not found: %s', kf_path);
    end
    T_kf = readmatrix(kf_path);
    if size(T_kf, 1) ~= 5
        error('run_3d_forward_swing:keyframes_csv', ...
            'keyframes CSV must have 5 rows (got %d).', size(T_kf, 1));
    end
    if size(T_kf, 2) ~= numel(params.swing.phase_t)
        error('run_3d_forward_swing:keyframes_csv', ...
            'keyframes CSV must have %d columns to match phase_t.', ...
            numel(params.swing.phase_t));
    end
    params.swing.q_keyframes_deg = T_kf;
end

% --------- sim grid + joint trajectories ---------------------------------
t_sim = (0:params.dt:params.t_end)';
sw    = min_jerk_swing(t_sim, params);
N_sim = numel(t_sim);

% --------- forward kinematics + racket-head velocity at every step -------
shoulder_pos = zeros(N_sim, 3);
elbow_pos    = zeros(N_sim, 3);
wrist_pos    = zeros(N_sim, 3);
racket_pos   = zeros(N_sim, 3);
shoulder_q   = zeros(N_sim, 4);
elbow_q      = zeros(N_sim, 4);
wrist_q      = zeros(N_sim, 4);
racket_q     = zeros(N_sim, 4);
face_n       = zeros(N_sim, 3);
racket_speed = zeros(N_sim, 1);

for k = 1:N_sim
    q_k  = sw.q(k, :)';
    pose = racket_pose_from_joints(q_k, params);
    f    = pose.frames;
    shoulder_pos(k, :) = quat_utils('T_pos', f.shoulder)';
    elbow_pos(k, :)    = quat_utils('T_pos', f.elbow)';
    wrist_pos(k, :)    = quat_utils('T_pos', f.wrist)';
    racket_pos(k, :)   = pose.head_pos';
    shoulder_q(k, :)   = quat_utils('rotmat2quat', quat_utils('T_rot', f.shoulder))';
    elbow_q(k, :)      = quat_utils('rotmat2quat', quat_utils('T_rot', f.forearm))';
    wrist_q(k, :)      = quat_utils('rotmat2quat', quat_utils('T_rot', f.racket_orient))';
    racket_q(k, :)     = pose.head_quat';
    face_n(k, :)       = pose.face_normal';
    Jk = jacobian_5dof(q_k, params);
    racket_speed(k) = norm(Jk * sw.qd(k, :)');
end

% --------- ball flight: pre-impact ---------------------------------------
[~, k_contact] = min(abs(t_sim - params.swing.contact_t));
pre_t = t_sim(1:k_contact);
[~, ball_pre] = ball_dynamics_3d(pre_t, ...
    params.ball.p0, params.ball.v0, params.ball.spin0, params.ball);

% --------- impact at k_contact -------------------------------------------
Jc            = jacobian_5dof(sw.q(k_contact, :)', params);
v_racket_world = Jc * sw.qd(k_contact, :)';
ball_in   = struct('velocity', ball_pre(end, 4:6)', ...
                   'spin',     params.ball.spin0(:), ...
                   'mass',     params.ball.mass, ...
                   'radius',   params.ball.radius);
racket_in = struct('velocity', v_racket_world, ...
                   'normal',   face_n(k_contact, :)');
[v_post, spin_post] = ball_racket_collision(ball_in, racket_in, params.ball);

% --------- ball flight: post-impact --------------------------------------
post_t = t_sim(k_contact:end);
[~, ball_post] = ball_dynamics_3d(post_t, ...
    ball_pre(end, 1:3)', v_post, spin_post, params.ball);

% --------- stitch full ball trace to the sim grid ------------------------
ball_pos_all = [ball_pre(1:end-1, 1:3); ball_post(:, 1:3)];
ball_vel_all = [ball_pre(1:end-1, 4:6); ball_post(:, 4:6)];
spin_all     = repmat(params.ball.spin0(:)', N_sim, 1);
spin_all(k_contact:end, :) = repmat(spin_post(:)', N_sim - k_contact + 1, 1);

contact_flag_sim = zeros(N_sim, 1);
contact_flag_sim(k_contact) = 1;

% --------- resample to Unity FPS -----------------------------------------
n_step = max(1, round((1 / params.unity_fps) / params.dt));
sel    = unique([1:n_step:N_sim, N_sim], 'stable');
Nf     = numel(sel);

frames = struct();
frames.frame              = (0:Nf-1)';
frames.t_s                = t_sim(sel);
frames.phase_id           = sw.phase_id(sel);
frames.phase_label        = sw.phase(sel);
frames.phase_t            = sw.phase_t(:);
frames.shoulder_pos       = shoulder_pos(sel, :);
frames.shoulder_quat      = shoulder_q(sel, :);
frames.elbow_pos          = elbow_pos(sel, :);
frames.elbow_quat         = elbow_q(sel, :);
frames.wrist_pos          = wrist_pos(sel, :);
frames.wrist_quat         = wrist_q(sel, :);
frames.racket_pos         = racket_pos(sel, :);
frames.racket_quat        = racket_q(sel, :);
frames.racket_face_normal = face_n(sel, :);
frames.racket_speed_mps   = racket_speed(sel);
frames.q                  = sw.q(sel, :);
frames.ball_pos           = ball_pos_all(sel, :);
frames.ball_vel           = ball_vel_all(sel, :);
frames.ball_spin          = spin_all(sel, :);
frames.contact_flag       = contact_flag_sim(sel);

% Make sure the Unity-rate stream still has at least one contact frame.
if ~any(frames.contact_flag)
    [~, kc_unity] = min(abs(frames.t_s - params.swing.contact_t));
    frames.contact_flag(kc_unity) = 1;
end

% --------- output dir + writers ------------------------------------------
out_dir = fullfile(params.output_root, params.export.experiment_name, ...
    params.export.run_id);
if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end
csv_path    = fullfile(out_dir, 'states.csv');
jsonl_path  = fullfile(out_dir, 'states.jsonl');
schema_path = fullfile(out_dir, 'schema.json');

if params.export.write_csv
    export_unity_swing_csv(csv_path, frames);
end
if params.export.write_jsonl
    export_unity_swing_jsonl(jsonl_path, frames);
end

% Schema sidecar with run-level summary so any consumer can sanity-check
% the run without parsing every frame.
schema = unity_coords('schema_meta');
schema.dof_mode                 = params.dof_mode;
schema.run_id                   = params.export.run_id;
schema.experiment_name          = params.export.experiment_name;
schema.dt_sim_s                 = params.dt;
schema.unity_fps                = params.unity_fps;
schema.t_end_s                  = params.t_end;
schema.contact_t_s              = params.swing.contact_t;
schema.shoulder_pos_world       = params.physics.shoulder_pos_world(:)';
schema.ball_v0                  = params.ball.v0(:)';
schema.ball_v_post_impact       = v_post(:)';
schema.ball_spin_post           = spin_post(:)';
schema.racket_speed_at_contact_mps = norm(v_racket_world);
schema.peak_racket_speed_mps    = max(racket_speed);
schema.frame_count              = Nf;
fid = fopen(schema_path, 'w');
fprintf(fid, '%s\n', jsonencode(schema));
fclose(fid);

% --------- optional plot --------------------------------------------------
if logical(opts.plot)
    plot_path = fullfile(out_dir, 'swing_3d.png');
    try
        plot_swing_3d(frames, ball_pre, ball_post, plot_path);
    catch err
        warning('run_3d_forward_swing:plot', ...
            'plot_swing_3d failed: %s', err.message);
    end
end

% --------- optional UDP stream -------------------------------------------
if logical(opts.stream)
    stream_swing_udp(jsonl_path, ...
        params.streaming.host, params.streaming.port, ...
        params.streaming.fps, params.streaming.realtime);
end

% --------- results --------------------------------------------------------
results = struct();
results.params   = params;
results.frames   = frames;
results.ball_pre  = ball_pre;
results.ball_post = ball_post;
results.contact = struct( ...
    't_s',               params.swing.contact_t, ...
    'racket_speed_mps',  norm(v_racket_world), ...
    'face_normal',       face_n(k_contact, :), ...
    'ball_v_pre',        ball_pre(end, 4:6), ...
    'ball_v_post',       v_post(:)', ...
    'ball_spin_post',    spin_post(:)');
results.out_dir = out_dir;
results.csv     = csv_path;
results.jsonl   = jsonl_path;
results.schema  = schema_path;

fprintf(['[run_3d_forward_swing] dof_mode=%s | %d frames @ %d Hz | ', ...
    'racket_speed_at_contact=%.2f m/s | peak=%.2f m/s\n'], ...
    params.dof_mode, Nf, params.unity_fps, ...
    results.contact.racket_speed_mps, max(racket_speed));
fprintf('[run_3d_forward_swing] outputs: %s\n', out_dir);
end
