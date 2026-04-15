function [time, state] = ball_trajectory_simulator(ball_initial, ball_params, t_final, options)
%BALL_TRAJECTORY_SIMULATOR Simulates tennis ball trajectory with aerodynamics
%
% This function simulates the 3D trajectory of a tennis ball including:
% - Gravity
% - Aerodynamic drag
% - Magnus effect (spin-induced lift)
%
% Inputs:
%   ball_initial - Structure with initial conditions:
%                  .position - Initial position [x; y; z] (m) - 3x1 vector
%                  .velocity - Initial velocity [vx; vy; vz] (m/s) - 3x1 vector
%                  .spin     - Angular velocity [wx; wy; wz] (rad/s) - 3x1 vector
%   ball_params  - Structure with ball parameters:
%                  .mass   - Ball mass (kg), default 0.057
%                  .radius - Ball radius (m), default 0.0335
%                  .Cd     - Drag coefficient, default 0.55
%                  .Cl     - Lift coefficient (Magnus), default 0.25
%                  .rho    - Air density (kg/m^3), default 1.225
%                  .g      - Gravitational acceleration (m/s^2), default 9.81
%   t_final      - Final simulation time (s), default 3.0
%   options      - (Optional) Structure with solver options:
%                  .dt     - Time step (s), default 0.001
%                  .method - Integration method: 'ode45' or 'euler', default 'ode45'
%
% Outputs:
%   time  - Time vector (s) - Nx1 vector
%   state - State matrix [x, y, z, vx, vy, vz] - Nx6 matrix
%
% Example:
%   ball_initial.position = [0; 1; 0];
%   ball_initial.velocity = [20; 5; 0];
%   ball_initial.spin = [0; 0; -100];  % Topspin
%   ball_params.mass = 0.057;
%   ball_params.radius = 0.0335;
%   ball_params.Cd = 0.55;
%   ball_params.Cl = 0.25;
%   ball_params.rho = 1.225;
%   ball_params.g = 9.81;
%   [time, state] = ball_trajectory_simulator(ball_initial, ball_params, 2.0);
%
% Author: PhD Research Model
% Date: 2024

%% Input Validation
if nargin < 2
    error('ball_trajectory_simulator:NotEnoughInputs', ...
          ['Not enough input arguments.\n' ...
           'Usage: [time, state] = ball_trajectory_simulator(ball_initial, ball_params, t_final)\n' ...
           'Run "help ball_trajectory_simulator" for more information.']);
end

% Set defaults
if nargin < 3 || isempty(t_final)
    t_final = 3.0;
end
if nargin < 4
    options = struct();
end

% Validate ball_initial structure
if ~isfield(ball_initial, 'position') || ~isfield(ball_initial, 'velocity')
    error('ball_trajectory_simulator:InvalidInitial', ...
          'ball_initial must contain .position and .velocity fields');
end

if ~isfield(ball_initial, 'spin')
    ball_initial.spin = [0; 0; 0];  % No spin by default
end

% Validate ball_params structure and set defaults
if ~isfield(ball_params, 'mass'),   ball_params.mass = 0.057;   end
if ~isfield(ball_params, 'radius'), ball_params.radius = 0.0335; end
if ~isfield(ball_params, 'Cd'),     ball_params.Cd = 0.55;      end
if ~isfield(ball_params, 'Cl'),     ball_params.Cl = 0.25;      end
if ~isfield(ball_params, 'rho'),    ball_params.rho = 1.225;    end
if ~isfield(ball_params, 'g'),      ball_params.g = 9.81;       end

% Set solver options
if ~isfield(options, 'dt'),     options.dt = 0.001;      end
if ~isfield(options, 'method'), options.method = 'ode45'; end

%% Extract Parameters
m = ball_params.mass;
r = ball_params.radius;
Cd = ball_params.Cd;
Cl = ball_params.Cl;
rho = ball_params.rho;
g = ball_params.g;

% Cross-sectional area
A = pi * r^2;

% Spin vector (assumed constant during flight)
omega = ball_initial.spin(:);

%% Initial State
pos0 = ball_initial.position(:);
vel0 = ball_initial.velocity(:);
y0 = [pos0; vel0];  % State vector: [x; y; z; vx; vy; vz]

%% Define Dynamics Function
    function dydt = ball_dynamics(~, y)
        % Extract state
        % pos = y(1:3);  % Position (not used in dynamics)
        vel = y(4:6);  % Velocity
        
        v_mag = norm(vel);
        
        if v_mag < 1e-6
            % Avoid division by zero
            dydt = [vel; 0; -g; 0];
            return;
        end
        
        % Unit velocity vector
        v_hat = vel / v_mag;
        
        % Drag force: F_d = -0.5 * rho * Cd * A * |v|^2 * v_hat
        F_drag = -0.5 * rho * Cd * A * v_mag^2 * v_hat;
        
        % Magnus force: F_m = 0.5 * rho * Cl * A * r * |omega| * |v| * (omega_hat x v_hat)
        omega_mag = norm(omega);
        if omega_mag > 1e-6
            omega_hat = omega / omega_mag;
            % Magnus force direction is perpendicular to both spin axis and velocity
            magnus_dir = cross(omega_hat, v_hat);
            magnus_mag = 0.5 * rho * Cl * A * r * omega_mag * v_mag;
            F_magnus = magnus_mag * magnus_dir;
        else
            F_magnus = [0; 0; 0];
        end
        
        % Gravity force: F_g = [0; -m*g; 0] (y is vertical)
        F_gravity = [0; -m*g; 0];
        
        % Total force
        F_total = F_drag + F_magnus + F_gravity;
        
        % Acceleration
        accel = F_total / m;
        
        % State derivative
        dydt = [vel; accel];
    end

%% Simulate Trajectory
switch lower(options.method)
    case 'ode45'
        % Use MATLAB's adaptive ODE solver
        [time, state] = ode45(@ball_dynamics, [0, t_final], y0);
        
    case 'euler'
        % Fixed-step Euler integration
        dt = options.dt;
        N = ceil(t_final / dt) + 1;
        time = (0:dt:t_final)';
        state = zeros(length(time), 6);
        state(1,:) = y0';
        
        for i = 1:length(time)-1
            dydt = ball_dynamics(time(i), state(i,:)');
            state(i+1,:) = state(i,:) + dt * dydt';
            
            % Stop if ball hits ground (y <= 0)
            if state(i+1,2) <= 0
                time = time(1:i+1);
                state = state(1:i+1,:);
                break;
            end
        end
        
    otherwise
        error('ball_trajectory_simulator:InvalidMethod', ...
              'Unknown integration method: %s. Use ''ode45'' or ''euler''.', options.method);
end

%% Post-process: Stop at ground contact
ground_idx = find(state(:,2) < 0, 1);
if ~isempty(ground_idx) && ground_idx > 1
    % Interpolate to find exact ground contact
    t1 = time(ground_idx-1);
    t2 = time(ground_idx);
    y1 = state(ground_idx-1, 2);
    y2 = state(ground_idx, 2);
    
    % Linear interpolation for ground contact time
    t_ground = t1 + (0 - y1) * (t2 - t1) / (y2 - y1);
    
    % Trim data
    time = [time(1:ground_idx-1); t_ground];
    
    % Interpolate state at ground contact
    alpha = (t_ground - t1) / (t2 - t1);
    state_ground = state(ground_idx-1,:) + alpha * (state(ground_idx,:) - state(ground_idx-1,:));
    state_ground(2) = 0;  % Exactly at ground
    
    state = [state(1:ground_idx-1,:); state_ground];
end

end
