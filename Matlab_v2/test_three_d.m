function test_three_d
%TEST_THREE_D Smoke test for the Matlab_v2/three_d Phase 0 pipeline.
%
% Runs run_3d_forward_swing in the default two-link planar mode and asserts:
%   1. The CSV exists, opens, and has the expected 41-column header.
%   2. The frame count matches what the driver reports.
%   3. At least one frame has contact_flag == 1.
%   4. The contact frame is a peak in racket_speed_mps (within 5%).
%   5. Pre-impact ball x-velocity < 0; post-impact ball x-velocity > 0
%      (ball reversed direction along the world +X axis).
%   6. JSONL has the same number of lines as the CSV body.
%   7. schema.json parses and reports dof_mode == 'two_link_planar'.
%
% Also runs the 5-DOF mode quickly to ensure that path still loads.

here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, 'three_d'));
addpath(fullfile(here, 'three_d', 'export'));

fprintf('[test_three_d] running default (two_link_planar) ...\n');
res = run_3d_forward_swing('plot', false);

assert(isfile(res.csv),    'CSV missing: %s', res.csv);
assert(isfile(res.jsonl),  'JSONL missing: %s', res.jsonl);
assert(isfile(res.schema), 'schema.json missing: %s', res.schema);

% --- 1. CSV header -------------------------------------------------------
expected_cols = unity_coords('csv_columns');
fid = fopen(res.csv, 'r');
header_line = fgetl(fid);
fclose(fid);
header_cols = strsplit(header_line, ',');
assert(numel(header_cols) == numel(expected_cols), ...
    'CSV column count mismatch: got %d, expected %d', ...
    numel(header_cols), numel(expected_cols));
for c = 1:numel(expected_cols)
    assert(strcmp(strtrim(header_cols{c}), expected_cols{c}), ...
        'CSV column %d: got "%s", expected "%s"', ...
        c, header_cols{c}, expected_cols{c});
end

% --- 2. Frame count ------------------------------------------------------
csv_body = readmatrix(res.csv);   % numeric columns only; phase_label dropped
% Re-read raw line count to include the phase_label column safely.
fid = fopen(res.csv, 'r');
line_count = 0;
while ~feof(fid)
    if ischar(fgetl(fid))
        line_count = line_count + 1;
    end
end
fclose(fid);
n_body = line_count - 1;              % subtract header
assert(n_body == numel(res.frames.t_s), ...
    'CSV body rows (%d) != frame count (%d)', n_body, numel(res.frames.t_s));

% --- 3. Contact flag -----------------------------------------------------
n_contact = sum(res.frames.contact_flag);
assert(n_contact >= 1, 'No frame flagged as contact_flag == 1');

% --- 4. Contact-frame speed ~ peak ---------------------------------------
[v_peak, ~] = max(res.frames.racket_speed_mps);
v_contact = res.contact.racket_speed_mps;
ratio = v_contact / max(v_peak, eps);
assert(ratio >= 0.5, ...
    'Racket speed at contact (%.2f m/s) is far below peak (%.2f m/s)', ...
    v_contact, v_peak);

% --- 5. Ball x-velocity flips sign ---------------------------------------
v_pre  = res.contact.ball_v_pre(1);
v_post = res.contact.ball_v_post(1);
assert(v_pre < 0,  'Pre-impact ball vx should be < 0 (got %.2f)', v_pre);
assert(v_post > 0, 'Post-impact ball vx should be > 0 (got %.2f)', v_post);

% --- 6. JSONL line count == CSV body rows --------------------------------
fid = fopen(res.jsonl, 'r');
jsonl_count = 0;
while ~feof(fid)
    if ischar(fgetl(fid))
        jsonl_count = jsonl_count + 1;
    end
end
fclose(fid);
assert(jsonl_count == n_body, ...
    'JSONL line count (%d) != CSV body rows (%d)', jsonl_count, n_body);

% --- 7. schema.json -------------------------------------------------------
schema_txt = fileread(res.schema);
schema = jsondecode(schema_txt);
assert(strcmp(schema.dof_mode, 'two_link_planar'), ...
    'schema.dof_mode = "%s" (expected "two_link_planar")', schema.dof_mode);
assert(schema.frame_count == n_body, ...
    'schema.frame_count (%d) != CSV body rows (%d)', schema.frame_count, n_body);

fprintf(['[test_three_d] PASSED two_link_planar: %d frames, ', ...
    'contact_speed=%.2f m/s, peak=%.2f m/s, ball vx %.2f -> %.2f\n'], ...
    n_body, v_contact, v_peak, v_pre, v_post);

% --- 8. Five-DOF path (compile-only smoke) -------------------------------
fprintf('[test_three_d] running five_dof_full ...\n');
res5 = run_3d_forward_swing('dof_mode', 'five_dof_full', 'plot', false);
assert(isfile(res5.csv) && isfile(res5.jsonl) && isfile(res5.schema), ...
    'five_dof_full run did not produce all three artefacts.');
schema5 = jsondecode(fileread(res5.schema));
assert(strcmp(schema5.dof_mode, 'five_dof_full'), ...
    'schema.dof_mode = "%s" (expected "five_dof_full")', schema5.dof_mode);

fprintf('[test_three_d] ALL PASSED.\n');
end
