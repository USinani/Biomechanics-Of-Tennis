function [v_ee, J] = end_effector_velocity(q, qd, params, phi, phi_dot)
%END_EFFECTOR_VELOCITY Planar EE velocity (m/s); optional pronation phi, phi_dot (rad, rad/s).
if nargin < 4 || isempty(phi)
    phi = 0;
end
if nargin < 5 || isempty(phi_dot)
    phi_dot = 0;
end
qd = qd(:);
q = q(:);
if numel(q) ~= 2 || numel(qd) ~= 2
    error('end_effector_velocity:dim', 'q and qd must be 2x1');
end
q1 = q(1);
q2e = q(2) + phi;
l1 = params.physics.l1;
l2 = params.physics.l2;
J = zeros(2, 2);
J(1,1) = -l1 * sin(q1) - l2 * sin(q1 + q2e);
J(1,2) = -l2 * sin(q1 + q2e);
J(2,1) = l1 * cos(q1) + l2 * cos(q1 + q2e);
J(2,2) = l2 * cos(q1 + q2e);
effective_q2dot = qd(2) + phi_dot;
v_ee = J * [qd(1); effective_q2dot];
end
