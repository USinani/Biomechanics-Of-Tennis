%% TEST_ALL_FUNCTIONS - Dynamics + legacy helpers + canonical run_swing_sim
thisdir = fileparts(mfilename('fullpath'));
addpath(genpath(thisdir));

fprintf('=======================================================\n');
fprintf('  Matlab_v2 verification\n');
fprintf('=======================================================\n\n');

errors_found = 0;

%% Test 1: two_link_tennis_model
fprintf('Test 1: two_link_tennis_model... ');
try
    params = struct();
    params.l1 = 0.30; params.l2 = 0.35;
    params.m1 = 2.0; params.m2 = 1.5;
    params.lc1 = 0.15; params.lc2 = 0.20;
    params.I1 = 0.025; params.I2 = 0.045;
    params.g = 9.81;
    theta = [0.5; 0.3];
    theta_dot = [1.0; 0.5];
    [M, C, G, B] = two_link_tennis_model(theta, theta_dot, params);
    assert(all(size(M) == [2, 2]));
    assert(all(size(C) == [2, 2]));
    assert(all(size(G) == [2, 1]));
    assert(all(size(B) == [2, 2]));
    assert(norm(M - M', 'fro') < 1e-10);
    assert(all(eig(M) > 0));
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 2: three_link_tennis_model (legacy)
fprintf('Test 2: three_link_tennis_model... ');
try
    params = struct();
    params.l1 = 0.30; params.l2 = 0.25; params.l3 = 0.68;
    params.m1 = 2.0; params.m2 = 1.2; params.m3 = 0.34;
    params.lc1 = 0.15; params.lc2 = 0.12; params.lc3 = 0.34;
    params.I1 = 0.025; params.I2 = 0.015; params.I3 = 0.015;
    params.g = 9.81;
    theta = [0.5; 0.3; 0.1];
    theta_dot = [1.0; 0.5; 0.2];
    [M, C, G, B] = three_link_tennis_model(theta, theta_dot, params);
    assert(all(size(M) == [3, 3]));
    assert(norm(M - M', 'fro') < 1e-10);
    assert(all(eig(M) > 0));
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 3: compute_inverse_dynamics
fprintf('Test 3: compute_inverse_dynamics... ');
try
    params = struct();
    params.l1 = 0.30; params.l2 = 0.35;
    params.m1 = 2.0; params.m2 = 1.5;
    params.lc1 = 0.15; params.lc2 = 0.20;
    params.I1 = 0.025; params.I2 = 0.045;
    params.g = 9.81;
    theta = [0.5; 0.3];
    theta_dot = [1.0; 0.5];
    theta_ddot = [5.0; 3.0];
    tau = compute_inverse_dynamics(theta, theta_dot, theta_ddot, params);
    assert(all(size(tau) == [2, 1]));
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 4: compute_forward_dynamics
fprintf('Test 4: compute_forward_dynamics... ');
try
    params = struct();
    params.l1 = 0.30; params.l2 = 0.35;
    params.m1 = 2.0; params.m2 = 1.5;
    params.lc1 = 0.15; params.lc2 = 0.20;
    params.I1 = 0.025; params.I2 = 0.045;
    params.g = 9.81;
    theta = [0.5; 0.3];
    theta_dot = [1.0; 0.5];
    tau = [10.0; 5.0];
    theta_ddot = compute_forward_dynamics(theta, theta_dot, tau, params);
    assert(all(size(theta_ddot) == [2, 1]));
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 5: Forward-inverse consistency
fprintf('Test 5: Forward-inverse consistency... ');
try
    params = struct();
    params.l1 = 0.30; params.l2 = 0.35;
    params.m1 = 2.0; params.m2 = 1.5;
    params.lc1 = 0.15; params.lc2 = 0.20;
    params.I1 = 0.025; params.I2 = 0.045;
    params.g = 9.81;
    theta = [0.5; 0.3];
    theta_dot = [1.0; 0.5];
    theta_ddot_desired = [5.0; 3.0];
    tau = compute_inverse_dynamics(theta, theta_dot, theta_ddot_desired, params);
    theta_ddot_recovered = compute_forward_dynamics(theta, theta_dot, tau, params);
    error_norm = norm(theta_ddot_desired - theta_ddot_recovered);
    assert(error_norm < 1e-10);
    fprintf('PASSED (error = %.2e)\n', error_norm);
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 6: ball_trajectory_simulator
fprintf('Test 6: ball_trajectory_simulator... ');
try
    ball_initial = struct();
    ball_initial.position = [0; 1.5; 0];
    ball_initial.velocity = [20; 5; 0];
    ball_initial.spin = [0; 0; -50];
    ball_params = struct();
    ball_params.mass = 0.057;
    ball_params.radius = 0.0335;
    ball_params.Cd = 0.55;
    ball_params.Cl = 0.25;
    ball_params.rho = 1.225;
    ball_params.g = 9.81;
    [time, state] = ball_trajectory_simulator(ball_initial, ball_params, 1.0);
    assert(length(time) > 1);
    assert(size(state, 2) == 6);
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 7: ball_racket_toy
fprintf('Test 7: ball_racket_toy... ');
try
    ball_state = struct();
    ball_state.position = [0; 1; 0];
    ball_state.velocity = [-20; 0; 0];
    ball_state.spin = [0; 0; -50];
    ball_state.mass = 0.057;
    ball_state.radius = 0.0335;
    racket_state = struct();
    racket_state.position = [0; 1; 0];
    racket_state.velocity = [30; 5; 0];
    racket_state.normal = [1; 0; 0];
    ball_params = struct();
    ball_params.e = 0.75;
    ball_params.mu = 0.4;
    [post_vel, post_spin] = ball_racket_toy(ball_state, racket_state, ball_params);
    assert(post_vel(1) > 0);
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 8: generate_enhanced_summary_report
fprintf('Test 8: generate_enhanced_summary_report... ');
try
    results = struct();
    results.time = (0:0.01:0.5)';
    results.params_2link = struct('l1', 0.3, 'l2', 0.35, 'm1', 2, 'm2', 1.5);
    results.two_link = struct();
    results.two_link.theta = rand(length(results.time), 2);
    results.two_link.theta_dot = rand(length(results.time), 2);
    results.two_link.tau = rand(length(results.time), 2) * 10;
    results.two_link.racket_speed = rand(length(results.time), 1) * 30;
    generate_enhanced_summary_report(results, 'test_report.txt');
    assert(exist('test_report.txt', 'file') == 2);
    delete('test_report.txt');
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

%% Test 9: run_swing_sim (canonical)
fprintf('Test 9: run_swing_sim... ');
try
    p = default_params();
    p.control.tau_amp = 2;
    p.t_end = 0.2;
    [t, x, u_hist, y, metrics] = run_swing_sim(p);
    assert(numel(t) > 5);
    assert(size(x, 2) == 4);
    assert(isfield(metrics, 'peak_ee_speed'));
    fprintf('PASSED\n');
catch ME
    fprintf('FAILED: %s\n', ME.message);
    errors_found = errors_found + 1;
end

fprintf('\n=======================================================\n');
if errors_found == 0
    fprintf('  ALL TESTS PASSED! (9/9)\n');
else
    fprintf('  Failures: %d\n', errors_found);
end
fprintf('=======================================================\n');
