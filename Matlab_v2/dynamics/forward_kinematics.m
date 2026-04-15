function p_ee = forward_kinematics(q, params, phi)
%FORWARD_KINEMATICS End-effector position in shoulder frame (m), planar x-y.
% phi (rad): optional pronation proxy added to distal joint angle (Option A).
if nargin < 3 || isempty(phi)
    phi = 0;
end
q = q(:);
if numel(q) ~= 2
    error('forward_kinematics:q', 'q must be 2x1');
end
q1 = q(1);
q2e = q(2) + phi;
l1 = params.physics.l1;
l2 = params.physics.l2;
px = l1 * cos(q1) + l2 * cos(q1 + q2e);
py = l1 * sin(q1) + l2 * sin(q1 + q2e);
p_ee = [px; py];
end
