function [t_out, state_out] = ball_dynamics_3d(t_grid, p0, v0, spin0, ball_params)
%BALL_DYNAMICS_3D Tennis ball flight in 3D, Z-up world (gravity in -Z).
%
% Forces:
%   - Gravity:    F_g = [0; 0; -m*g]
%   - Drag:       F_d = -0.5 * rho * Cd * A * |v|^2 * v_hat
%   - Magnus:     F_m = 0.5 * rho * Cl * A * r * |omega| * |v| * (omega_hat x v_hat)
%
% Inputs:
%   t_grid       - Nx1 time grid (s); state_out is interpolated to it
%   p0           - 3x1 initial position (m)
%   v0           - 3x1 initial velocity (m/s)
%   spin0        - 3x1 angular velocity (rad/s); assumed constant in flight
%   ball_params  - struct (.mass .radius .Cd .Cl .rho .g)
%
% Outputs:
%   t_out        - same grid as t_grid (Nx1)
%   state_out    - Nx6 [px py pz vx vy vz]
%
% Integration: ode45 over [t_grid(1), t_grid(end)] with deval onto t_grid.
% No ground termination here; the swing window is short enough that the
% ball stays above the court. Trim post-hoc if needed.

t_grid = t_grid(:);
p0 = p0(:);  v0 = v0(:);  spin0 = spin0(:);
m   = ball_params.mass;
r   = ball_params.radius;
Cd  = ball_params.Cd;
Cl  = ball_params.Cl;
rho = ball_params.rho;
g   = ball_params.g;

A = pi * r^2;
omega = spin0;
omega_mag = norm(omega);
if omega_mag > 0
    omega_hat = omega / omega_mag;
else
    omega_hat = [0; 0; 0];
end

y0 = [p0; v0];
sol = ode45(@dyn, [t_grid(1), t_grid(end)], y0);
t_out = t_grid;
state_out = deval(sol, t_grid).';

    function dydt = dyn(~, y)
        v = y(4:6);
        v_mag = norm(v);
        if v_mag < 1e-9
            F = [0; 0; -m*g];
        else
            v_hat = v / v_mag;
            F_drag = -0.5 * rho * Cd * A * v_mag^2 * v_hat;
            if omega_mag > 0
                F_magnus = 0.5 * rho * Cl * A * r * omega_mag * v_mag * cross(omega_hat, v_hat);
            else
                F_magnus = [0; 0; 0];
            end
            F = F_drag + F_magnus + [0; 0; -m*g];
        end
        a = F / m;
        dydt = [v; a];
    end
end
