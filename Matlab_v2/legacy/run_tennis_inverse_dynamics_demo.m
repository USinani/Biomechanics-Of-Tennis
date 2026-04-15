%% RUN_TENNIS_INVERSE_DYNAMICS_DEMO - Legacy prescribed-trajectory + ball pipeline
% Canonical torque-driven benchmark: use main.m / run_swing_sim instead.
thisdir = fileparts(mfilename('fullpath'));
root = fileparts(thisdir);
addpath(genpath(root));

clear; clc; close all;

fprintf('=======================================================\n');
fprintf('  Tennis Biomechanics Simulation - PhD Research Model\n');
fprintf('=======================================================\n\n');

%% 1. Initialize Anthropometric Parameters (Two-Link Model)
fprintf('Initializing two-link arm parameters...\n');

params_2link = struct();

% Segment lengths (m)
params_2link.l1 = 0.30;    % Upper arm length
params_2link.l2 = 0.35;    % Forearm + racket length

% Segment masses (kg)
params_2link.m1 = 2.0;     % Upper arm mass
params_2link.m2 = 1.5;     % Forearm + racket mass

% Center of mass positions (fraction of segment length from proximal end)
params_2link.lc1 = 0.15;   % Upper arm COM distance
params_2link.lc2 = 0.20;   % Forearm + racket COM distance

% Moments of inertia about COM (kg*m^2)
params_2link.I1 = 0.025;   % Upper arm moment of inertia
params_2link.I2 = 0.045;   % Forearm + racket moment of inertia

% Gravity
params_2link.g = 9.81;     % Gravitational acceleration (m/s^2)

%% 2. Initialize Anthropometric Parameters (Three-Link Model)
fprintf('Initializing three-link arm parameters...\n');

params_3link = struct();

% Segment lengths (m)
params_3link.l1 = 0.30;    % Upper arm length
params_3link.l2 = 0.25;    % Forearm length
params_3link.l3 = 0.68;    % Racket length

% Segment masses (kg)
params_3link.m1 = 2.0;     % Upper arm mass
params_3link.m2 = 1.2;     % Forearm mass
params_3link.m3 = 0.34;    % Racket mass

% Center of mass positions (m from proximal end)
params_3link.lc1 = 0.15;   % Upper arm COM distance
params_3link.lc2 = 0.12;   % Forearm COM distance
params_3link.lc3 = 0.34;   % Racket COM distance

% Moments of inertia about COM (kg*m^2)
params_3link.I1 = 0.025;   % Upper arm moment of inertia
params_3link.I2 = 0.015;   % Forearm moment of inertia
params_3link.I3 = 0.015;   % Racket moment of inertia

% Gravity
params_3link.g = 9.81;

%% 3. Define Swing Trajectory (Time and Joint Angles)
fprintf('Generating swing trajectory...\n');

% Time parameters
t_start = 0;
t_end = 0.5;           % 500ms swing duration
dt = 0.001;            % 1ms time step
time = (t_start:dt:t_end)';
N = length(time);

% Generate smooth swing trajectory using minimum jerk profile
% Shoulder angle (theta1): from -30 deg to 90 deg (horizontal adduction)
theta1_start = deg2rad(-30);
theta1_end = deg2rad(90);

% Elbow angle (theta2): from 90 deg to 10 deg (extension)
theta2_start = deg2rad(90);
theta2_end = deg2rad(10);

% Wrist angle (theta3 for 3-link): from -20 deg to 30 deg (flexion)
theta3_start = deg2rad(-20);
theta3_end = deg2rad(30);

% Minimum jerk trajectory (smooth motion)
tau = (time - t_start) / (t_end - t_start);  % Normalized time [0,1]
s = 10*tau.^3 - 15*tau.^4 + 6*tau.^5;        % Position profile
s_dot = (30*tau.^2 - 60*tau.^3 + 30*tau.^4) / (t_end - t_start);  % Velocity
s_ddot = (60*tau - 180*tau.^2 + 120*tau.^3) / (t_end - t_start)^2; % Acceleration

% Two-link joint trajectories
theta_2link = zeros(N, 2);
theta_dot_2link = zeros(N, 2);
theta_ddot_2link = zeros(N, 2);

theta_2link(:,1) = theta1_start + (theta1_end - theta1_start) * s;
theta_2link(:,2) = theta2_start + (theta2_end - theta2_start) * s;

theta_dot_2link(:,1) = (theta1_end - theta1_start) * s_dot;
theta_dot_2link(:,2) = (theta2_end - theta2_start) * s_dot;

theta_ddot_2link(:,1) = (theta1_end - theta1_start) * s_ddot;
theta_ddot_2link(:,2) = (theta2_end - theta2_start) * s_ddot;

% Three-link joint trajectories
theta_3link = zeros(N, 3);
theta_dot_3link = zeros(N, 3);
theta_ddot_3link = zeros(N, 3);

theta_3link(:,1) = theta1_start + (theta1_end - theta1_start) * s;
theta_3link(:,2) = theta2_start + (theta2_end - theta2_start) * s;
theta_3link(:,3) = theta3_start + (theta3_end - theta3_start) * s;

theta_dot_3link(:,1) = (theta1_end - theta1_start) * s_dot;
theta_dot_3link(:,2) = (theta2_end - theta2_start) * s_dot;
theta_dot_3link(:,3) = (theta3_end - theta3_start) * s_dot;

theta_ddot_3link(:,1) = (theta1_end - theta1_start) * s_ddot;
theta_ddot_3link(:,2) = (theta2_end - theta2_start) * s_ddot;
theta_ddot_3link(:,3) = (theta3_end - theta3_start) * s_ddot;

%% 4. Compute Inverse Dynamics (Two-Link Model)
fprintf('Computing inverse dynamics (two-link model)...\n');

tau_2link = zeros(N, 2);  % Joint torques

for i = 1:N
    theta = theta_2link(i,:)';
    theta_dot = theta_dot_2link(i,:)';
    theta_ddot = theta_ddot_2link(i,:)';
    
    % Get dynamics matrices
    [M, C, G, ~] = two_link_tennis_model(theta, theta_dot, params_2link);
    
    % Inverse dynamics: tau = M*theta_ddot + C*theta_dot + G
    tau_2link(i,:) = (M * theta_ddot + C * theta_dot + G)';
end

%% 5. Compute Inverse Dynamics (Three-Link Model)
fprintf('Computing inverse dynamics (three-link model)...\n');

tau_3link = zeros(N, 3);  % Joint torques

for i = 1:N
    theta = theta_3link(i,:)';
    theta_dot = theta_dot_3link(i,:)';
    theta_ddot = theta_ddot_3link(i,:)';
    
    % Get dynamics matrices
    [M, C, G, ~] = three_link_tennis_model(theta, theta_dot, params_3link);
    
    % Inverse dynamics: tau = M*theta_ddot + C*theta_dot + G
    tau_3link(i,:) = (M * theta_ddot + C * theta_dot + G)';
end

%% 6. Compute Forward Dynamics Verification
fprintf('Verifying with forward dynamics...\n');

% Use computed torques to simulate forward dynamics and verify
theta_fwd = zeros(N, 2);
theta_dot_fwd = zeros(N, 2);

theta_fwd(1,:) = theta_2link(1,:);
theta_dot_fwd(1,:) = theta_dot_2link(1,:);

for i = 1:N-1
    theta = theta_fwd(i,:)';
    theta_dot_curr = theta_dot_fwd(i,:)';
    tau = tau_2link(i,:)';
    
    % Forward dynamics to get acceleration
    theta_ddot_curr = compute_forward_dynamics(theta, theta_dot_curr, tau, params_2link);
    
    % Euler integration
    theta_dot_fwd(i+1,:) = theta_dot_curr' + theta_ddot_curr' * dt;
    theta_fwd(i+1,:) = theta' + theta_dot_curr' * dt;
end

%% 7. Compute End-Effector (Racket) Kinematics
fprintf('Computing end-effector kinematics...\n');

% Two-link end-effector position and velocity
x_ee = zeros(N, 2);
v_ee = zeros(N, 2);

for i = 1:N
    % End-effector position
    x_ee(i,1) = params_2link.l1 * cos(theta_2link(i,1)) + ...
                params_2link.l2 * cos(theta_2link(i,1) + theta_2link(i,2));
    x_ee(i,2) = params_2link.l1 * sin(theta_2link(i,1)) + ...
                params_2link.l2 * sin(theta_2link(i,1) + theta_2link(i,2));
    
    % Jacobian
    J = zeros(2,2);
    J(1,1) = -params_2link.l1 * sin(theta_2link(i,1)) - ...
              params_2link.l2 * sin(theta_2link(i,1) + theta_2link(i,2));
    J(1,2) = -params_2link.l2 * sin(theta_2link(i,1) + theta_2link(i,2));
    J(2,1) = params_2link.l1 * cos(theta_2link(i,1)) + ...
             params_2link.l2 * cos(theta_2link(i,1) + theta_2link(i,2));
    J(2,2) = params_2link.l2 * cos(theta_2link(i,1) + theta_2link(i,2));
    
    % End-effector velocity
    v_ee(i,:) = (J * theta_dot_2link(i,:)')';
end

% Racket speed at impact
racket_speed = sqrt(v_ee(:,1).^2 + v_ee(:,2).^2);
[max_speed, max_idx] = max(racket_speed);
fprintf('  Maximum racket speed: %.2f m/s at t = %.3f s\n', max_speed, time(max_idx));

%% 8. Ball Trajectory Simulation
fprintf('Simulating ball trajectory...\n');

% Ball parameters
ball_params = struct();
ball_params.mass = 0.057;      % Tennis ball mass (kg)
ball_params.radius = 0.0335;   % Tennis ball radius (m)
ball_params.Cd = 0.55;         % Drag coefficient
ball_params.Cl = 0.25;         % Lift coefficient (for spin)
ball_params.rho = 1.225;       % Air density (kg/m^3)
ball_params.g = 9.81;          % Gravity (m/s^2)
ball_params.e = 0.75;          % Coefficient of restitution

% Initial ball conditions (incoming ball)
ball_initial = struct();
ball_initial.position = [12; 1.5; 0];   % Starting position (m) - from opponent
ball_initial.velocity = [-20; 2; 0];     % Initial velocity (m/s) - towards player
ball_initial.spin = [0; 0; -50];         % Spin (rad/s) - topspin

% Simulate ball trajectory
[ball_time, ball_state] = ball_trajectory_simulator(ball_initial, ball_params, 2.0);

fprintf('  Ball trajectory simulated for %.2f seconds\n', ball_time(end));

%% 9. Ball-Racket Impact Analysis
fprintf('Analyzing ball-racket impact...\n');

% Find impact point (when ball reaches x = 0.5m, approximate racket position)
impact_idx = find(ball_state(:,1) < 0.5, 1);
if ~isempty(impact_idx)
    impact_pos = ball_state(impact_idx, 1:3);
    impact_vel = ball_state(impact_idx, 4:6);
    fprintf('  Impact position: [%.2f, %.2f, %.2f] m\n', impact_pos);
    fprintf('  Ball velocity at impact: %.2f m/s\n', norm(impact_vel));
    
    % Simulate impact using ball_racket_toy model
    racket_state = struct();
    racket_state.position = [0.5; 1.2; 0];  % Racket position at impact
    racket_state.velocity = [max_speed; 5; 0];  % Racket velocity
    racket_state.normal = [1; 0.2; 0];  % Racket face normal
    racket_state.normal = racket_state.normal / norm(racket_state.normal);
    
    ball_state_impact = struct();
    ball_state_impact.position = impact_pos';
    ball_state_impact.velocity = impact_vel';
    ball_state_impact.spin = ball_initial.spin;
    ball_state_impact.mass = ball_params.mass;
    ball_state_impact.radius = ball_params.radius;
    
    % Compute post-impact ball velocity
    [post_velocity, post_spin] = ball_racket_toy(ball_state_impact, racket_state, ball_params);
    
    fprintf('  Post-impact ball velocity: %.2f m/s\n', norm(post_velocity));
    fprintf('  Post-impact ball spin: %.2f rad/s\n', norm(post_spin));
end

%% 10. Generate Visualizations
fprintf('\nGenerating visualizations...\n');

% Figure 1: Joint angles
figure('Name', 'Joint Angles', 'Position', [100, 100, 1200, 400]);

subplot(1,3,1);
plot(time, rad2deg(theta_2link(:,1)), 'b-', 'LineWidth', 2);
hold on;
plot(time, rad2deg(theta_2link(:,2)), 'r-', 'LineWidth', 2);
xlabel('Time (s)');
ylabel('Angle (degrees)');
title('Two-Link Model: Joint Angles');
legend('Shoulder', 'Elbow');
grid on;

subplot(1,3,2);
plot(time, rad2deg(theta_3link(:,1)), 'b-', 'LineWidth', 2);
hold on;
plot(time, rad2deg(theta_3link(:,2)), 'r-', 'LineWidth', 2);
plot(time, rad2deg(theta_3link(:,3)), 'g-', 'LineWidth', 2);
xlabel('Time (s)');
ylabel('Angle (degrees)');
title('Three-Link Model: Joint Angles');
legend('Shoulder', 'Elbow', 'Wrist');
grid on;

subplot(1,3,3);
plot(time, racket_speed, 'k-', 'LineWidth', 2);
xlabel('Time (s)');
ylabel('Speed (m/s)');
title('Racket Head Speed');
grid on;

% Figure 2: Joint torques
figure('Name', 'Joint Torques', 'Position', [100, 550, 1200, 400]);

subplot(1,2,1);
plot(time, tau_2link(:,1), 'b-', 'LineWidth', 2);
hold on;
plot(time, tau_2link(:,2), 'r-', 'LineWidth', 2);
xlabel('Time (s)');
ylabel('Torque (Nm)');
title('Two-Link Model: Joint Torques');
legend('Shoulder', 'Elbow');
grid on;

subplot(1,2,2);
plot(time, tau_3link(:,1), 'b-', 'LineWidth', 2);
hold on;
plot(time, tau_3link(:,2), 'r-', 'LineWidth', 2);
plot(time, tau_3link(:,3), 'g-', 'LineWidth', 2);
xlabel('Time (s)');
ylabel('Torque (Nm)');
title('Three-Link Model: Joint Torques');
legend('Shoulder', 'Elbow', 'Wrist');
grid on;

% Figure 3: Arm animation snapshots
figure('Name', 'Swing Animation', 'Position', [100, 100, 800, 600]);

num_frames = 6;
frame_indices = round(linspace(1, N, num_frames));

for f = 1:num_frames
    subplot(2,3,f);
    idx = frame_indices(f);
    
    % Plot arm segments
    x0 = 0; y0 = 0;
    x1 = params_2link.l1 * cos(theta_2link(idx,1));
    y1 = params_2link.l1 * sin(theta_2link(idx,1));
    x2 = x1 + params_2link.l2 * cos(theta_2link(idx,1) + theta_2link(idx,2));
    y2 = y1 + params_2link.l2 * sin(theta_2link(idx,1) + theta_2link(idx,2));
    
    plot([x0, x1], [y0, y1], 'b-', 'LineWidth', 3);
    hold on;
    plot([x1, x2], [y1, y2], 'r-', 'LineWidth', 3);
    plot(x0, y0, 'ko', 'MarkerSize', 10, 'MarkerFaceColor', 'k');
    plot(x1, y1, 'bo', 'MarkerSize', 8, 'MarkerFaceColor', 'b');
    plot(x2, y2, 'ro', 'MarkerSize', 8, 'MarkerFaceColor', 'r');
    
    axis equal;
    xlim([-0.2, 0.8]);
    ylim([-0.4, 0.6]);
    title(sprintf('t = %.3f s', time(idx)));
    grid on;
end
sgtitle('Tennis Swing Animation (Two-Link Model)');

% Figure 4: Ball trajectory
if ~isempty(impact_idx)
    figure('Name', 'Ball Trajectory', 'Position', [900, 100, 600, 500]);
    plot3(ball_state(1:impact_idx,1), ball_state(1:impact_idx,3), ball_state(1:impact_idx,2), ...
          'b-', 'LineWidth', 2);
    hold on;
    plot3(ball_state(1,1), ball_state(1,3), ball_state(1,2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g');
    plot3(ball_state(impact_idx,1), ball_state(impact_idx,3), ball_state(impact_idx,2), ...
          'ro', 'MarkerSize', 10, 'MarkerFaceColor', 'r');
    xlabel('X (m)');
    ylabel('Z (m)');
    zlabel('Y (m)');
    title('Ball Trajectory (Before Impact)');
    legend('Trajectory', 'Start', 'Impact');
    grid on;
    view(30, 20);
end

%% 11. Store Results
fprintf('\nStoring results...\n');

results = struct();
results.time = time;
results.params_2link = params_2link;
results.params_3link = params_3link;
results.ball_params = ball_params;

results.two_link = struct();
results.two_link.theta = theta_2link;
results.two_link.theta_dot = theta_dot_2link;
results.two_link.theta_ddot = theta_ddot_2link;
results.two_link.tau = tau_2link;
results.two_link.x_ee = x_ee;
results.two_link.v_ee = v_ee;
results.two_link.racket_speed = racket_speed;

results.three_link = struct();
results.three_link.theta = theta_3link;
results.three_link.theta_dot = theta_dot_3link;
results.three_link.theta_ddot = theta_ddot_3link;
results.three_link.tau = tau_3link;

results.ball = struct();
results.ball.time = ball_time;
results.ball.state = ball_state;
results.ball.initial = ball_initial;

% Save to file
save('tennis_simulation_results.mat', 'results');

%% 12. Generate Summary Report
fprintf('\nGenerating summary report...\n');
generate_enhanced_summary_report(results);

%% Summary
fprintf('\n=======================================================\n');
fprintf('  Simulation Complete!\n');
fprintf('=======================================================\n');
fprintf('\nKey Results:\n');
fprintf('  - Maximum racket speed: %.2f m/s\n', max_speed);
fprintf('  - Peak shoulder torque (2-link): %.2f Nm\n', max(abs(tau_2link(:,1))));
fprintf('  - Peak elbow torque (2-link): %.2f Nm\n', max(abs(tau_2link(:,2))));
fprintf('  - Peak shoulder torque (3-link): %.2f Nm\n', max(abs(tau_3link(:,1))));
fprintf('  - Peak elbow torque (3-link): %.2f Nm\n', max(abs(tau_3link(:,2))));
fprintf('  - Peak wrist torque (3-link): %.2f Nm\n', max(abs(tau_3link(:,3))));
fprintf('\nResults saved to: tennis_simulation_results.mat\n');
fprintf('Figures generated for visualization.\n');
