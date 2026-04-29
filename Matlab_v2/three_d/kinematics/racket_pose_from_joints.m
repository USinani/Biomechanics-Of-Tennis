function pose = racket_pose_from_joints(q, params)
%RACKET_POSE_FROM_JOINTS Convenience wrapper: q -> racket head world pose.
%
% Inputs:
%   q      - 5x1 joint vector (rad)
%   params - struct from default_params_3d
%
% Output:
%   pose.head_pos        - 3x1 racket head centre in world (m)
%   pose.head_quat       - 4x1 quaternion [w;x;y;z] of racket head frame
%   pose.face_normal     - 3x1 unit vector of racket face normal in world
%   pose.shaft_axis      - 3x1 unit vector along racket shaft (forearm +X)
%   pose.frames          - full struct from fk_5dof_arm

frames = fk_5dof_arm(q, params);
T = frames.racket_orient;          % orientation frame at the wrist tip
R = quat_utils('T_rot', T);

pose.head_pos    = quat_utils('T_pos', frames.racket_head);
pose.head_quat   = quat_utils('rotmat2quat', R);
pose.shaft_axis  = R(:, 1);        % racket shaft = local +X
pose.face_normal = R(:, 3);        % racket face normal = local +Z
pose.frames      = frames;
end
