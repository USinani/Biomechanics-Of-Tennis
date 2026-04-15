function theta_ddot = compute_forward_dynamics(theta, theta_dot, tau, params)
%COMPUTE_FORWARD_DYNAMICS theta_ddot = M\(tau - C*qd - G); n=2 or n=3.
theta = theta(:);
theta_dot = theta_dot(:);
tau = tau(:);
n = numel(theta);
if numel(theta_dot) ~= n || numel(tau) ~= n
    error('compute_forward_dynamics:DimensionMismatch', 'theta, theta_dot, tau same length');
end
if n == 2
    [M, C, G, ~] = two_link_tennis_model(theta, theta_dot, params);
elseif n == 3
    [M, C, G, ~] = three_link_tennis_model(theta, theta_dot, params);
else
    error('compute_forward_dynamics:UnsupportedModel', 'n must be 2 or 3, got %d', n);
end
theta_ddot = M \ (tau - C * theta_dot - G);
theta_ddot = theta_ddot(:);
end
