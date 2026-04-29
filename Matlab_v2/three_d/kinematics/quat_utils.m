function out = quat_utils(op, varargin)
%QUAT_UTILS Quaternion + rotation utilities (RHS, unit quaternions, w-x-y-z order).
%
% Single dispatcher so the three_d module has zero toolbox dependencies.
% Convention: q = [w; x; y; z], unit, right-handed. Rotation R rotates
% vectors expressed in body frame into the world/parent frame.
%
% Supported ops:
%   R = quat_utils('Rx', theta)         3x3 rotation about x by theta (rad)
%   R = quat_utils('Ry', theta)         3x3 rotation about y by theta (rad)
%   R = quat_utils('Rz', theta)         3x3 rotation about z by theta (rad)
%   q = quat_utils('rotmat2quat', R)    R (3x3) -> q ([w;x;y;z], 4x1)
%   R = quat_utils('quat2rotmat', q)    q (4x1) -> R (3x3)
%   T = quat_utils('trans', p)          4x4 homogeneous translation
%   T = quat_utils('rot_to_T', R)       4x4 from 3x3 (no translation)
%   p = quat_utils('T_pos', T)          extract translation column from T
%   R = quat_utils('T_rot', T)          extract rotation block from T

if nargin < 1
    error('quat_utils:NotEnoughInputs', 'Operation name required.');
end
switch lower(op)
    case 'rx'
        theta = varargin{1};
        c = cos(theta); s = sin(theta);
        out = [1 0 0; 0 c -s; 0 s c];
    case 'ry'
        theta = varargin{1};
        c = cos(theta); s = sin(theta);
        out = [c 0 s; 0 1 0; -s 0 c];
    case 'rz'
        theta = varargin{1};
        c = cos(theta); s = sin(theta);
        out = [c -s 0; s c 0; 0 0 1];
    case 'rotmat2quat'
        R = varargin{1};
        out = local_rotmat2quat(R);
    case 'quat2rotmat'
        q = varargin{1};
        out = local_quat2rotmat(q);
    case 'trans'
        p = varargin{1}(:);
        out = eye(4);
        out(1:3, 4) = p;
    case 'rot_to_t'
        R = varargin{1};
        out = eye(4);
        out(1:3, 1:3) = R;
    case 't_pos'
        T = varargin{1};
        out = T(1:3, 4);
    case 't_rot'
        T = varargin{1};
        out = T(1:3, 1:3);
    otherwise
        error('quat_utils:UnknownOp', 'Unknown op: %s', op);
end
end

function q = local_rotmat2quat(R)
% Shepperd 1978 / Shoemake quaternion extraction; numerically stable.
trace_R = R(1, 1) + R(2, 2) + R(3, 3);
if trace_R > 0
    s = sqrt(trace_R + 1.0) * 2;
    qw = 0.25 * s;
    qx = (R(3, 2) - R(2, 3)) / s;
    qy = (R(1, 3) - R(3, 1)) / s;
    qz = (R(2, 1) - R(1, 2)) / s;
elseif (R(1, 1) > R(2, 2)) && (R(1, 1) > R(3, 3))
    s = sqrt(1.0 + R(1, 1) - R(2, 2) - R(3, 3)) * 2;
    qw = (R(3, 2) - R(2, 3)) / s;
    qx = 0.25 * s;
    qy = (R(1, 2) + R(2, 1)) / s;
    qz = (R(1, 3) + R(3, 1)) / s;
elseif R(2, 2) > R(3, 3)
    s = sqrt(1.0 + R(2, 2) - R(1, 1) - R(3, 3)) * 2;
    qw = (R(1, 3) - R(3, 1)) / s;
    qx = (R(1, 2) + R(2, 1)) / s;
    qy = 0.25 * s;
    qz = (R(2, 3) + R(3, 2)) / s;
else
    s = sqrt(1.0 + R(3, 3) - R(1, 1) - R(2, 2)) * 2;
    qw = (R(2, 1) - R(1, 2)) / s;
    qx = (R(1, 3) + R(3, 1)) / s;
    qy = (R(2, 3) + R(3, 2)) / s;
    qz = 0.25 * s;
end
q = [qw; qx; qy; qz];
n = norm(q);
if n > 0
    q = q / n;
end
end

function R = local_quat2rotmat(q)
q = q(:);
n = norm(q);
if n > 0
    q = q / n;
end
w = q(1); x = q(2); y = q(3); z = q(4);
R = [ ...
    1 - 2*(y*y + z*z),  2*(x*y - z*w),     2*(x*z + y*w); ...
    2*(x*y + z*w),      1 - 2*(x*x + z*z), 2*(y*z - x*w); ...
    2*(x*z - y*w),      2*(y*z + x*w),     1 - 2*(x*x + y*y)];
end
