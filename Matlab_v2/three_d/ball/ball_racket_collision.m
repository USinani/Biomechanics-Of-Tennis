function [v_post, spin_post] = ball_racket_collision(ball, racket, params)
%BALL_RACKET_COLLISION 3D impulse-based ball-racket impact (Z-up).
%
% Inputs:
%   ball   - struct (.velocity 3x1, .spin 3x1, .mass, .radius)
%   racket - struct (.velocity 3x1, .normal 3x1 unit face normal)
%   params - struct (.e coef of restitution, .mu Coulomb friction)
%
% Outputs:
%   v_post     - 3x1 post-impact ball velocity (world frame, m/s)
%   spin_post  - 3x1 post-impact ball angular velocity (rad/s)
%
% Model (Cross 2014, generalised, Z-up):
%   - Contact point is on the ball at -r * n from the centre.
%   - Normal impulse from coefficient of restitution.
%   - Tangential impulse from Coulomb friction limit.
%   - Racket assumed massive vs ball.

m  = ball.mass;
r  = ball.radius;
e  = params.e;
mu = params.mu;
I  = (2/5) * m * r^2;        % solid-sphere moment

v_b   = ball.velocity(:);
w_b   = ball.spin(:);
v_r   = racket.velocity(:);
n     = racket.normal(:);
n_mag = norm(n);
if n_mag < 1e-9
    error('ball_racket_collision:n', 'racket.normal must be non-zero.');
end
n = n / n_mag;

% Relative velocity of the ball-surface point at the contact relative to
% the racket: v_contact = v_b - v_r + omega_b x (-r * n)
v_contact = v_b - v_r + cross(w_b, -r * n);
v_n_scalar = dot(v_contact, n);

% No impact if ball is moving away from the racket along the face normal.
if v_n_scalar >= 0
    v_post    = v_b;
    spin_post = w_b;
    return;
end

j_n_scalar = -(1 + e) * m * v_n_scalar;
j_n        = j_n_scalar * n;

v_t = v_contact - v_n_scalar * n;
v_t_mag = norm(v_t);
if v_t_mag > 1e-9
    t_hat   = -v_t / v_t_mag;
    m_eff_t = 1 / (1/m + r^2/I);
    j_t_need = m_eff_t * v_t_mag;
    j_t_max  = mu * abs(j_n_scalar);
    j_t      = min(j_t_need, j_t_max) * t_hat;
else
    j_t = [0; 0; 0];
end

j = j_n + j_t;
v_post    = v_b + j / m + v_r;
spin_post = w_b + cross(-r * n, j) / I;
end
