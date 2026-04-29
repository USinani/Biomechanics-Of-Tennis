function export_unity_swing_csv(filepath, frames)
%EXPORT_UNITY_SWING_CSV Write per-Unity-frame swing data (RHS Z-up).
%
% Inputs:
%   filepath - destination CSV path
%   frames   - struct array OR struct-of-arrays with fields matching
%              unity_coords('csv_columns'). See run_3d_forward_swing for
%              the canonical builder.

cols = unity_coords('csv_columns');
[fid, msg] = fopen(filepath, 'w');
if fid < 0
    error('export_unity_swing_csv:open', 'Cannot open %s: %s', filepath, msg);
end
cleanup = onCleanup(@() fclose(fid));

% Header
fprintf(fid, '%s', cols{1});
for c = 2:numel(cols)
    fprintf(fid, ',%s', cols{c});
end
fprintf(fid, '\n');

N = numel(frames.t_s);
for k = 1:N
    fprintf(fid, '%d,%.6f,%d,%s', ...
        frames.frame(k), frames.t_s(k), ...
        frames.phase_id(k), frames.phase_label{k});
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.shoulder_pos(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f,%.6f', frames.shoulder_quat(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.elbow_pos(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f,%.6f', frames.elbow_quat(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.wrist_pos(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f,%.6f', frames.wrist_quat(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.racket_pos(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f,%.6f', frames.racket_quat(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.racket_face_normal(k, :));
    fprintf(fid, ',%.6f', frames.racket_speed_mps(k));
    fprintf(fid, ',%.6f,%.6f,%.6f,%.6f,%.6f', frames.q(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.ball_pos(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.ball_vel(k, :));
    fprintf(fid, ',%.6f,%.6f,%.6f', frames.ball_spin(k, :));
    fprintf(fid, ',%d\n', frames.contact_flag(k));
end
end
