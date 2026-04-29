function J = jacobian_5dof(q, params, eps_h)
%JACOBIAN_5DOF Numerical 3x5 Jacobian of racket-head position wrt q.
%
% Central-difference finite differences. Returned J maps qdot -> v_head:
%   v_head_world = J * qdot
%
% Sufficient for Phase 0 (kinematic playback). Phase 1 should replace this
% with an analytical body Jacobian when forward dynamics is added.

if nargin < 3 || isempty(eps_h)
    eps_h = 1e-6;
end
q = q(:);
n = numel(q);
J = zeros(3, n);
for i = 1:n
    qp = q;  qp(i) = qp(i) + eps_h;
    qm = q;  qm(i) = qm(i) - eps_h;
    pose_p = racket_pose_from_joints(qp, params);
    pose_m = racket_pose_from_joints(qm, params);
    J(:, i) = (pose_p.head_pos - pose_m.head_pos) / (2 * eps_h);
end
end
