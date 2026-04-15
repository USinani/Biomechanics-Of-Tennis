function tau = compute_inverse_dynamics(theta, theta_dot, theta_ddot, params)
%COMPUTE_INVERSE_DYNAMICS Computes required torques for desired motion
%
% This function solves the inverse dynamics problem: given the desired
% motion trajectory (joint angles, velocities, and accelerations), compute
% the required joint torques.
%
% Inverse dynamics equation: tau = M*theta_ddot + C*theta_dot + G
%
% Inputs:
%   theta      - Joint angles (rad) - nx1 vector where n is number of joints
%   theta_dot  - Joint angular velocities (rad/s) - nx1 vector
%   theta_ddot - Joint angular accelerations (rad/s^2) - nx1 vector
%   params     - Structure containing model parameters (see two_link_tennis_model)
%
% Outputs:
%   tau - Required joint torques (Nm) - nx1 vector
%
% Example (2-link model):
%   params.l1 = 0.3; params.l2 = 0.35; params.m1 = 2; params.m2 = 1.5;
%   params.lc1 = 0.15; params.lc2 = 0.2; params.I1 = 0.025; params.I2 = 0.045;
%   params.g = 9.81;
%   theta = [0.5; 0.3]; theta_dot = [1; 0.5]; theta_ddot = [5; 3];
%   tau = compute_inverse_dynamics(theta, theta_dot, theta_ddot, params);
%
% Author: PhD Research Model
% Date: 2024

%% Input Validation
if nargin < 4
    error('compute_inverse_dynamics:NotEnoughInputs', ...
          ['Not enough input arguments.\n' ...
           'Usage: tau = compute_inverse_dynamics(theta, theta_dot, theta_ddot, params)\n' ...
           'Run "help compute_inverse_dynamics" for more information.']);
end

% Ensure column vectors
theta = theta(:);
theta_dot = theta_dot(:);
theta_ddot = theta_ddot(:);

% Validate dimensions match
n = length(theta);
if length(theta_dot) ~= n || length(theta_ddot) ~= n
    error('compute_inverse_dynamics:DimensionMismatch', ...
          'theta, theta_dot, and theta_ddot must all have the same length');
end

%% Determine model type and compute dynamics matrices
if n == 2
    % Two-link model
    [M, C, G, ~] = two_link_tennis_model(theta, theta_dot, params);
elseif n == 3
    % Three-link model
    [M, C, G, ~] = three_link_tennis_model(theta, theta_dot, params);
else
    error('compute_inverse_dynamics:UnsupportedModel', ...
          'Only 2-link and 3-link models are currently supported (n = %d given)', n);
end

%% Compute Inverse Dynamics
% Inverse dynamics: tau = M * theta_ddot + C * theta_dot + G

tau = M * theta_ddot + C * theta_dot + G;

% Ensure output is a column vector
tau = tau(:);

end
