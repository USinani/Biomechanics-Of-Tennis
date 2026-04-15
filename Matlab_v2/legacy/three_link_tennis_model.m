function [M, C, G, B] = three_link_tennis_model(theta, theta_dot, params)
%THREE_LINK_TENNIS_MODEL Legacy 3-link planar arm (upper arm, forearm, racket).
% Kept for inverse-dynamics demo and tests; canonical swing benchmark is 2-DOF.
if nargin < 3
    error('three_link_tennis_model:NotEnoughInputs', ...
          'Usage: [M, C, G, B] = three_link_tennis_model(theta, theta_dot, params)');
end
if ~isnumeric(theta) || numel(theta) ~= 3
    error('three_link_tennis_model:InvalidTheta', 'theta must be a 3-element numeric vector');
end
if ~isnumeric(theta_dot) || numel(theta_dot) ~= 3
    error('three_link_tennis_model:InvalidThetaDot', 'theta_dot must be a 3-element numeric vector');
end
required_fields = {'l1', 'l2', 'l3', 'm1', 'm2', 'm3', 'lc1', 'lc2', 'lc3', 'I1', 'I2', 'I3', 'g'};
for i = 1:length(required_fields)
    if ~isfield(params, required_fields{i})
        error('three_link_tennis_model:MissingParam', 'params structure missing required field: %s', required_fields{i});
    end
end
l1 = params.l1;
l2 = params.l2;
l3 = params.l3;
m1 = params.m1;
m2 = params.m2;
m3 = params.m3;
lc1 = params.lc1;
lc2 = params.lc2;
lc3 = params.lc3;
I1 = params.I1;
I2 = params.I2;
I3 = params.I3;
g = params.g;
theta = theta(:);
theta_dot = theta_dot(:);
q1 = theta(1);
q2 = theta(2);
q3 = theta(3);
q1_dot = theta_dot(1);
q2_dot = theta_dot(2);
q3_dot = theta_dot(3);
c1 = cos(q1);
s1 = sin(q1);
c2 = cos(q2);
s2 = sin(q2);
c3 = cos(q3);
s3 = sin(q3);
c12 = cos(q1 + q2);
s12 = sin(q1 + q2);
c23 = cos(q2 + q3);
s23 = sin(q2 + q3);
c123 = cos(q1 + q2 + q3);
s123 = sin(q1 + q2 + q3);
a1 = I1 + I2 + I3 + m1*lc1^2 + m2*(l1^2 + lc2^2) + m3*(l1^2 + l2^2 + lc3^2);
a2 = m2*l1*lc2 + m3*l1*l2;
a3 = m3*l1*lc3;
a4 = I2 + I3 + m2*lc2^2 + m3*(l2^2 + lc3^2);
a5 = m3*l2*lc3;
a6 = I3 + m3*lc3^2;
M11 = a1 + 2*a2*c2 + 2*a3*c23 + 2*a5*c3;
M12 = a4 + a2*c2 + a3*c23 + 2*a5*c3;
M13 = a6 + a3*c23 + a5*c3;
M22 = a4 + 2*a5*c3;
M23 = a6 + a5*c3;
M33 = a6;
M = [M11, M12, M13; M12, M22, M23; M13, M23, M33];
h1 = -m2*l1*lc2*s2 - m3*l1*l2*s2;
h2 = -m3*l1*lc3*s23;
h3 = -m3*l2*lc3*s3;
C11 = h1*q2_dot + h2*(q2_dot + q3_dot) + h3*q3_dot;
C12 = h1*(q1_dot + q2_dot) + h2*(q1_dot + q2_dot + q3_dot) + h3*q3_dot;
C13 = h2*(q1_dot + q2_dot + q3_dot) + h3*(q1_dot + q2_dot + q3_dot);
C21 = -h1*q1_dot - h2*q1_dot;
C22 = h3*q3_dot;
C23 = h3*(q1_dot + q2_dot + q3_dot);
C31 = -h2*q1_dot - h3*(q1_dot + q2_dot);
C32 = -h3*(q1_dot + q2_dot);
C33 = 0;
C = [C11, C12, C13; C21, C22, C23; C31, C32, C33];
G1 = (m1*lc1 + m2*l1 + m3*l1)*g*c1 + (m2*lc2 + m3*l2)*g*c12 + m3*lc3*g*c123;
G2 = (m2*lc2 + m3*l2)*g*c12 + m3*lc3*g*c123;
G3 = m3*lc3*g*c123;
G = [G1; G2; G3];
B = eye(3);
end
