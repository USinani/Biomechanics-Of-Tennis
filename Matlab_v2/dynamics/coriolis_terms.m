function C = coriolis_terms(theta, theta_dot, params)
%CORIOLIS_TERMS Coriolis/centrifugal matrix C(q,qd) for two-link planar arm.
theta = theta(:);
theta_dot = theta_dot(:);
if numel(theta) ~= 2 || numel(theta_dot) ~= 2
    error('coriolis_terms:dim', 'theta and theta_dot must be 2x1');
end
theta1_dot = theta_dot(1);
theta2_dot = theta_dot(2);
theta2 = theta(2);
l1 = params.l1;
m2 = params.m2;
lc2 = params.lc2;
s2 = sin(theta2);
h = -m2*l1*lc2*s2;
C11 = h*theta2_dot;
C12 = h*(theta1_dot + theta2_dot);
C21 = -h*theta1_dot;
C22 = 0;
C = [C11, C12; C21, C22];
end
