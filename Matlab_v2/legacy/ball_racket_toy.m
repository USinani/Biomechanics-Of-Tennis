function [post_velocity, post_spin] = ball_racket_toy(ball_state, racket_state, ball_params)
%BALL_RACKET_TOY Computes ball velocity and spin after racket impact
%
% This function models the ball-racket impact using an impulse-based collision
% model that accounts for:
% - Coefficient of restitution (bounce)
% - Racket velocity transfer
% - Friction effects on spin
%
% Inputs:
%   ball_state   - Structure with ball state at impact:
%                  .position - Ball position [x; y; z] (m) - 3x1 vector
%                  .velocity - Ball velocity [vx; vy; vz] (m/s) - 3x1 vector
%                  .spin     - Ball angular velocity [wx; wy; wz] (rad/s) - 3x1 vector
%                  .mass     - Ball mass (kg)
%                  .radius   - Ball radius (m)
%   racket_state - Structure with racket state at impact:
%                  .position - Racket impact point [x; y; z] (m) - 3x1 vector
%                  .velocity - Racket velocity [vx; vy; vz] (m/s) - 3x1 vector
%                  .normal   - Racket face normal (unit vector) - 3x1 vector
%   ball_params  - Structure with impact parameters:
%                  .e  - Coefficient of restitution, default 0.75
%                  .mu - Coefficient of friction, default 0.4
%
% Outputs:
%   post_velocity - Ball velocity after impact (m/s) - 3x1 vector
%   post_spin     - Ball angular velocity after impact (rad/s) - 3x1 vector
%
% Example:
%   ball_state.position = [0; 1; 0];
%   ball_state.velocity = [-20; 0; 0];
%   ball_state.spin = [0; 0; -50];
%   ball_state.mass = 0.057;
%   ball_state.radius = 0.0335;
%   racket_state.position = [0; 1; 0];
%   racket_state.velocity = [30; 5; 0];
%   racket_state.normal = [1; 0; 0];
%   ball_params.e = 0.75;
%   [post_vel, post_spin] = ball_racket_toy(ball_state, racket_state, ball_params);
%
% Reference:
%   Cross, R. (2014). Impact of a ball with a bat or racket.
%   American Journal of Physics, 67(8), 692-702.
%
% Author: PhD Research Model
% Date: 2024

%% Input Validation
if nargin < 3
    error('ball_racket_toy:NotEnoughInputs', ...
          ['Not enough input arguments.\n' ...
           'Usage: [post_velocity, post_spin] = ball_racket_toy(ball_state, racket_state, ball_params)\n' ...
           'Run "help ball_racket_toy" for more information.']);
end

% Validate ball_state structure
required_ball_fields = {'velocity', 'spin', 'mass', 'radius'};
for i = 1:length(required_ball_fields)
    if ~isfield(ball_state, required_ball_fields{i})
        error('ball_racket_toy:InvalidBallState', ...
              'ball_state must contain .%s field', required_ball_fields{i});
    end
end

% Validate racket_state structure
required_racket_fields = {'velocity', 'normal'};
for i = 1:length(required_racket_fields)
    if ~isfield(racket_state, required_racket_fields{i})
        error('ball_racket_toy:InvalidRacketState', ...
              'racket_state must contain .%s field', required_racket_fields{i});
    end
end

% Set default parameters
if ~isfield(ball_params, 'e'),  ball_params.e = 0.75;  end  % Coefficient of restitution
if ~isfield(ball_params, 'mu'), ball_params.mu = 0.4;  end  % Coefficient of friction

%% Extract Parameters
m = ball_state.mass;
r = ball_state.radius;
e = ball_params.e;
mu = ball_params.mu;

% Moment of inertia for solid sphere: I = (2/5)*m*r^2
I = (2/5) * m * r^2;

% Velocities (ensure column vectors)
v_ball = ball_state.velocity(:);
omega_ball = ball_state.spin(:);
v_racket = racket_state.velocity(:);
n = racket_state.normal(:);

% Ensure normal is unit vector
n = n / norm(n);

%% Compute Relative Velocity at Contact Point
% Relative velocity of ball surface at contact point relative to racket
% v_rel = v_ball - v_racket + omega x (-r*n)
% Contact point on ball is at -r*n from ball center

v_contact = v_ball - v_racket + cross(omega_ball, -r*n);

% Decompose into normal and tangential components
v_n = dot(v_contact, n) * n;      % Normal component
v_t = v_contact - v_n;             % Tangential component

%% Compute Normal Impulse
% Normal impulse based on coefficient of restitution
% j_n = -(1 + e) * m * v_n / (1 + m*r^2/I)
% For a solid sphere impacting a massive racket (racket mass >> ball mass)

% Effective mass for normal impact
m_eff_n = m;

% Normal impulse magnitude (scalar, along normal direction)
v_n_scalar = dot(v_contact, n);
j_n_scalar = -(1 + e) * m_eff_n * v_n_scalar;

% Only apply if ball is approaching racket (v_n_scalar < 0)
if v_n_scalar >= 0
    % Ball moving away from racket, no impact
    post_velocity = v_ball;
    post_spin = omega_ball;
    return;
end

j_n = j_n_scalar * n;

%% Compute Tangential Impulse (Friction)
% Tangential impulse due to friction
% Limited by Coulomb friction: |j_t| <= mu * |j_n|

v_t_mag = norm(v_t);

if v_t_mag > 1e-6
    % Direction of tangential impulse (opposes sliding)
    t_hat = -v_t / v_t_mag;
    
    % Effective mass for tangential impact (includes rotational inertia)
    m_eff_t = 1 / (1/m + r^2/I);
    
    % Impulse needed to stop sliding
    j_t_needed = m_eff_t * v_t_mag;
    
    % Apply Coulomb friction limit
    j_t_max = mu * abs(j_n_scalar);
    j_t_mag = min(j_t_needed, j_t_max);
    
    j_t = j_t_mag * t_hat;
else
    j_t = [0; 0; 0];
end

%% Total Impulse
j_total = j_n + j_t;

%% Compute Post-Impact Velocity and Spin
% Linear velocity change: delta_v = j / m
post_velocity = v_ball + j_total / m + v_racket;

% Angular velocity change: delta_omega = (r x j) / I
% Torque arm is from ball center to contact point: -r*n
delta_omega = cross(-r*n, j_total) / I;
post_spin = omega_ball + delta_omega;

%% Apply racket angle effect on spin (simplified model)
% The racket angle affects the spin imparted to the ball
% This is a simplified model; real impact is more complex

% Racket tilt relative to horizontal affects topspin/backspin
% If racket face is tilted back, it imparts topspin
if abs(n(2)) < 0.99  % Not purely vertical impact
    % Estimate additional spin from racket angle
    racket_tilt = asin(n(2));  % Angle of racket face from vertical
    
    % Additional topspin component (around horizontal axis perpendicular to ball travel)
    ball_direction = v_ball / max(norm(v_ball), 1e-6);
    spin_axis = cross(ball_direction, [0; 1; 0]);
    if norm(spin_axis) > 1e-6
        spin_axis = spin_axis / norm(spin_axis);
        
        % Spin magnitude proportional to impact speed and racket tilt
        impact_speed = norm(v_racket);
        additional_spin = impact_speed * sin(racket_tilt) * 2;  % Empirical factor
        
        post_spin = post_spin + additional_spin * spin_axis;
    end
end

% Ensure outputs are column vectors
post_velocity = post_velocity(:);
post_spin = post_spin(:);

end
