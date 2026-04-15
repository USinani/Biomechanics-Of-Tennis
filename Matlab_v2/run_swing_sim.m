function [t, x, u_hist, y, metrics] = run_swing_sim(params)
%RUN_SWING_SIM Canonical forward simulation: open-loop torques, semi-implicit Euler.
% Matches example_two_link Python bridge integrator: qdd from (q,qd,tau), then
% qd_new = qd + qdd*dt, q_new = q + qd_new*dt.
%
% Outputs:
%   t      - Nx1 time (s)
%   x      - Nx4 state [q1 q2 dq1 dq2]
%   u_hist - Nx2 applied torques (N*m)
%   y      - struct: p_ee, v_ee, speed, phi, energy_total, ke1, ke2, pe
%   metrics - struct from compute_metrics

here = fileparts(mfilename('fullpath'));
addpath(genpath(here));

validate_params(params);
dt = params.dt;
t = (0:dt:params.t_end)';
N = numel(t);
x = zeros(N, 4);
% Row state [q1 q2 dq1 dq2]: horizontal concat (semicolon would stack to 2x2).
x(1, :) = [params.q0(:)', params.qd0(:)'];
u_hist = zeros(N, 2);

for k = 1:N - 1
    uk = control_profile(t(k), params);
    u_hist(k, :) = uk';
    xk = x(k, :)';
    q = xk(1:2);
    qd = xk(3:4);
    dx = two_link_dynamics(t(k), xk, params, uk);
    qdd = dx(3:4);
    qd_new = qd + qdd * dt;
    q_new = q + qd_new * dt;
    x(k + 1, :) = [q_new; qd_new]';
end
u_hist(N, :) = control_profile(t(end), params)';

y = build_derived_outputs(t, x, u_hist, params);
y.energy_transfer = compute_energy_transfer(t, x, u_hist, y, params);
metrics = compute_metrics(t, x, u_hist, y, params);

if isfield(params, 'export') && params.export.enable
    rid = params.export.run_id;
    if isempty(rid)
        rid = build_run_id(params.export.experiment_name);
        params.export.run_id = rid;
    end
    save_run_bundle(params, t, x, u_hist, y, metrics);
end
end

function y = build_derived_outputs(t, x, u_hist, params)
N = size(x, 1);
y.p_ee = zeros(N, 2);
y.v_ee = zeros(N, 2);
y.speed = zeros(N, 1);
y.phi = zeros(N, 1);
y.phi_dot = zeros(N, 1);
y.ke1 = zeros(N, 1);
y.ke2 = zeros(N, 1);
y.pe = zeros(N, 1);
y.energy_total = zeros(N, 1);
phys = params.physics;
I1 = phys.I1;
I2 = phys.I2;
m1 = phys.m1;
m2 = phys.m2;
g = phys.g;
lc1 = phys.lc1;
lc2 = phys.lc2;
for k = 1:N
    q = x(k, 1:2)';
    qd = x(k, 3:4)';
    tk = t(k);
    phi = pronation_profile(tk, params);
    phid = pronation_profile_derivative(tk, params);
    y.phi(k) = phi;
    y.phi_dot(k) = phid;
    y.p_ee(k, :) = forward_kinematics(q, params, phi)';
    [v_ee, ~] = end_effector_velocity(q, qd, params, phi, phid);
    y.v_ee(k, :) = v_ee';
    y.speed(k) = norm(v_ee);
    th1 = q(1);
    th2 = q(2);
    d1 = qd(1);
    d2 = qd(2);
    pe1 = m1 * g * lc1 * sin(th1);
    pe2 = m2 * g * (phys.l1 * sin(th1) + lc2 * sin(th1 + th2));
    y.pe(k) = pe1 + pe2;
    y.ke1(k) = 0.5 * I1 * d1^2 + 0.5 * m1 * (lc1 * d1)^2;
    v2_cm_x = -phys.l1 * sin(th1) * d1 - lc2 * sin(th1 + th2) * (d1 + d2);
    v2_cm_y = phys.l1 * cos(th1) * d1 + lc2 * cos(th1 + th2) * (d1 + d2);
    y.ke2(k) = 0.5 * m2 * (v2_cm_x^2 + v2_cm_y^2) + 0.5 * I2 * (d1 + d2)^2;
    y.energy_total(k) = y.ke1(k) + y.ke2(k) + y.pe(k);
end
end
