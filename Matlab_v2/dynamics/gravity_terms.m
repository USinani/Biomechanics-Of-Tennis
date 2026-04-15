function G = gravity_terms(theta, params)
%GRAVITY_TERMS Gravity vector G(q) (N*m) for two-link planar arm.
theta = theta(:);
if numel(theta) ~= 2
    error('gravity_terms:theta', 'theta must be 2x1');
end
theta1 = theta(1);
theta2 = theta(2);
g = params.g;
m1 = params.m1;
m2 = params.m2;
lc1 = params.lc1;
lc2 = params.lc2;
l1 = params.l1;
c1 = cos(theta1);
c12 = cos(theta1 + theta2);
G1 = (m1*lc1 + m2*l1)*g*c1 + m2*lc2*g*c12;
G2 = m2*lc2*g*c12;
G = [G1; G2];
end
