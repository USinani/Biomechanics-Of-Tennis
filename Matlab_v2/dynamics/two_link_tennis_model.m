function [M, C, G, B] = two_link_tennis_model(theta, theta_dot, params)
%TWO_LINK_TENNIS_MODEL Mass, Coriolis, gravity, input map (planar two-link).
% MATLAB = analytical benchmark; equations match example_two_link/matlab_v2_dynamics.py.
if nargin < 3
    error('two_link_tennis_model:NotEnoughInputs', 'Usage: [M,C,G,B] = two_link_tennis_model(theta, theta_dot, params)');
end
theta = theta(:);
theta_dot = theta_dot(:);
if numel(theta) ~= 2 || numel(theta_dot) ~= 2
    error('two_link_tennis_model:InvalidTheta', 'theta and theta_dot must be 2-element');
end
req = {'l1', 'l2', 'm1', 'm2', 'lc1', 'lc2', 'I1', 'I2', 'g'};
for i = 1:numel(req)
    if ~isfield(params, req{i})
        error('two_link_tennis_model:MissingParam', 'params missing field: %s', req{i});
    end
end
M = mass_matrix(theta, params);
C = coriolis_terms(theta, theta_dot, params);
G = gravity_terms(theta, params);
B = eye(2);
end
