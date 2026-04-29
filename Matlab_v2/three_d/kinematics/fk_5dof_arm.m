function frames = fk_5dof_arm(q, params)
%FK_5DOF_ARM 5-DOF forward kinematics for the tennis arm in 3D (RHS, Z-up).
%
% Joint vector q (5x1, rad):
%   q(1) = shoulder pitch  (about world Y)
%   q(2) = shoulder yaw    (about world Z)
%   q(3) = elbow flexion   (about local Y of upper-arm frame)
%   q(4) = forearm pronation (about local X = forearm long axis)
%   q(5) = wrist flexion   (about local Y of forearm-after-pronation frame)
%
% Returns a struct with 4x4 homogeneous transforms for every named frame:
%   frames.shoulder       - shoulder anchor (translation only)
%   frames.upperarm       - shoulder pos * Rz(q2) * Ry(q1)
%   frames.elbow          - upperarm * Trans([l1, 0, 0])
%   frames.forearm        - elbow * Ry(q3)
%   frames.forearm_pron   - forearm * Rx(q4)
%   frames.wrist          - forearm_pron * Trans([l2, 0, 0])
%   frames.racket_orient  - wrist * Ry(q5)
%   frames.racket_head    - racket_orient * Trans([l_racket, 0, 0])
%
% Conventions:
%   - All segment long axes point along local +X.
%   - Racket face normal is local +Z of frames.racket_orient (the strings
%     "look at" the +Z direction). Pronation rotates this face about the
%     forearm long axis; wrist flexion tilts it forward/back.

q = q(:);
if numel(q) ~= 5
    error('fk_5dof_arm:q', 'q must be 5x1 (got %d).', numel(q));
end
phys = params.physics;
l1 = phys.l_upperarm;
l2 = phys.l_forearm;
lr = phys.l_racket;
shoulder_pos = phys.shoulder_pos_world(:);

T_shoulder = quat_utils('trans', shoulder_pos);

R_pitch = quat_utils('Ry', q(1));
R_yaw   = quat_utils('Rz', q(2));
T_upperarm = T_shoulder * quat_utils('rot_to_T', R_yaw * R_pitch);

T_elbow = T_upperarm * quat_utils('trans', [l1; 0; 0]);

R_elbow = quat_utils('Ry', q(3));
T_forearm = T_elbow * quat_utils('rot_to_T', R_elbow);

R_pron = quat_utils('Rx', q(4));
T_forearm_pron = T_forearm * quat_utils('rot_to_T', R_pron);

T_wrist = T_forearm_pron * quat_utils('trans', [l2; 0; 0]);

R_wrist = quat_utils('Ry', q(5));
T_racket_orient = T_wrist * quat_utils('rot_to_T', R_wrist);

T_racket_head = T_racket_orient * quat_utils('trans', [lr; 0; 0]);

frames = struct( ...
    'shoulder',      T_shoulder, ...
    'upperarm',      T_upperarm, ...
    'elbow',         T_elbow, ...
    'forearm',       T_forearm, ...
    'forearm_pron',  T_forearm_pron, ...
    'wrist',         T_wrist, ...
    'racket_orient', T_racket_orient, ...
    'racket_head',   T_racket_head);
end
