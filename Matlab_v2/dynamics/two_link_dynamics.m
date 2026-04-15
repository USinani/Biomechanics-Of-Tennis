function dx = two_link_dynamics(t, x, params, u)
%TWO_LINK_DYNAMICS First-order ODE for two-link arm: x = [q1;q2;dq1;dq2].
% Optional viscous damping: tau_net = u - b.*qd (b in params.physics.damping_nm_s).
phys = params.physics;
q = x(1:2);
qd = x(3:4);
u = u(:);
if numel(u) ~= 2
    error('two_link_dynamics:u', 'u must be 2x1');
end
if isfield(phys, 'damping_nm_s') && ~isempty(phys.damping_nm_s)
    b = phys.damping_nm_s(:);
    if numel(b) == 1
        b = [b; b];
    end
    tau = u - b .* qd;
else
    tau = u;
end
qdd = compute_forward_dynamics(q, qd, tau, phys);
dx = [qd; qdd];
end
