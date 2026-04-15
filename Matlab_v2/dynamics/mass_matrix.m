function M = mass_matrix(theta, params)
%MASS_MATRIX Two-link planar arm mass matrix M(q) (kg*m^2).
% State q = [q1; q2] (rad), same equations as historical two_link_tennis_model.
theta = theta(:);
if numel(theta) ~= 2
    error('mass_matrix:theta', 'theta must be 2x1');
end
theta1 = theta(1);
theta2 = theta(2);
l1 = params.l1;
l2 = params.l2;
m1 = params.m1;
m2 = params.m2;
lc1 = params.lc1;
lc2 = params.lc2;
I1 = params.I1;
I2 = params.I2;
c2 = cos(theta2);
alpha = I1 + I2 + m1*lc1^2 + m2*(l1^2 + lc2^2);
beta = m2*l1*lc2;
delta = I2 + m2*lc2^2;
M11 = alpha + 2*beta*c2;
M12 = delta + beta*c2;
M22 = delta;
M = [M11, M12; M12, M22];
end
