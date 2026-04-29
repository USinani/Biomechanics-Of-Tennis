function swing = min_jerk_swing(t, params)
%MIN_JERK_SWING Piecewise minimum-jerk joint trajectories for the 5-DOF arm.
%
% Inputs:
%   t      - Nx1 time vector (s)
%   params - struct from default_params_3d (uses params.swing.{phase_t,
%            phase_labels, q_keyframes_deg})
%
% Outputs:
%   swing.q       - Nx5 joint angles (rad)
%   swing.qd      - Nx5 joint velocities (rad/s) (analytic from min-jerk)
%   swing.qdd     - Nx5 joint accelerations (rad/s^2)
%   swing.phase   - Nx1 cellstr phase label per sample
%   swing.phase_id - Nx1 integer phase index (1..numel(phase_labels))
%
% Convention:
%   - phase_t has length M+1 boundaries for M phases.
%   - q_keyframes_deg is 5xM+1: first column = pose at start of phase 1,
%     last column = pose at end of phase M, intermediate columns at each
%     boundary.
%   - Within each phase we use a quintic minimum-jerk profile
%       s(u) = 10*u^3 - 15*u^4 + 6*u^5,   u = (t - t0)/(t1 - t0)
%     so velocity and acceleration are zero at every keyframe.

t = t(:);
N = numel(t);
sw = params.swing;
phase_t = sw.phase_t(:)';
labels  = sw.phase_labels;
keys    = deg2rad(sw.q_keyframes_deg);  % 5x(M+1)

if size(keys, 1) ~= 5
    error('min_jerk_swing:keys', 'q_keyframes_deg must have 5 rows.');
end
M = numel(phase_t) - 1;
if size(keys, 2) ~= M + 1
    error('min_jerk_swing:keys_count', ...
        'q_keyframes_deg must have %d columns to match %d phases.', M + 1, M);
end
if numel(labels) ~= M
    error('min_jerk_swing:labels_count', ...
        'phase_labels must have %d entries.', M);
end

q   = zeros(N, 5);
qd  = zeros(N, 5);
qdd = zeros(N, 5);
phase    = cell(N, 1);
phase_id = zeros(N, 1);

for k = 1:N
    tk = t(k);
    p = max(1, min(M, find(phase_t <= tk + eps, 1, 'last')));
    if p < 1; p = 1; end
    if p > M; p = M; end
    t0 = phase_t(p);
    t1 = phase_t(p + 1);
    dT = max(t1 - t0, eps);
    u  = max(0, min(1, (tk - t0) / dT));
    s   = 10 * u^3 - 15 * u^4 + 6 * u^5;
    sd  = (30 * u^2 - 60 * u^3 + 30 * u^4) / dT;
    sdd = (60 * u    - 180 * u^2 + 120 * u^3) / (dT^2);
    qa = keys(:, p);
    qb = keys(:, p + 1);
    dq = qb - qa;
    q(k, :)   = (qa + dq * s)';
    qd(k, :)  = (dq * sd)';
    qdd(k, :) = (dq * sdd)';
    phase{k}    = labels{p};
    phase_id(k) = p;
end

swing = struct( ...
    'q', q, 'qd', qd, 'qdd', qdd, ...
    'phase', {phase}, 'phase_id', phase_id, ...
    'phase_t', phase_t, 'labels', {labels});
end
