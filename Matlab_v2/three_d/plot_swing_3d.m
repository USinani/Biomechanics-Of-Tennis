function fig = plot_swing_3d(frames, ball_pre, ball_post, savepath)
%PLOT_SWING_3D Four-panel figure summarising the 3D forward swing.
%
% Panels:
%   (1) 3D arm + racket trajectory (RHS Z-up) with phase-coloured racket
%       head trace and arm stick-figure snapshots.
%   (2) Racket head speed vs time, with phase shading.
%   (3) Joint angles vs time (deg).
%   (4) Ball trajectory before/after impact (3D).
%
% Inputs match the canonical builder in run_3d_forward_swing.

if nargin < 4
    savepath = '';
end

fig = figure('Name', '3D Forward Swing', 'Position', [80 80 1280 880], ...
    'Color', 'w');

t = frames.t_s;

% ---- Panel 1: 3D arm + racket trace -------------------------------------
ax1 = subplot(2, 2, 1);
hold(ax1, 'on'); grid(ax1, 'on'); axis(ax1, 'equal');
phase_colors = lines(max(frames.phase_id));
for k = 2:numel(t)
    c = phase_colors(frames.phase_id(k), :);
    plot3(ax1, frames.racket_pos(k-1:k, 1), frames.racket_pos(k-1:k, 2), ...
        frames.racket_pos(k-1:k, 3), '-', 'Color', c, 'LineWidth', 1.5);
end
% Stick-figure snapshots at 6 evenly spaced frames
N = numel(t);
snap = round(linspace(1, N, 6));
for s = snap
    pts = [frames.shoulder_pos(s, :); ...
           frames.elbow_pos(s, :); ...
           frames.wrist_pos(s, :); ...
           frames.racket_pos(s, :)];
    plot3(ax1, pts(:, 1), pts(:, 2), pts(:, 3), 'k-', 'LineWidth', 1.0);
    plot3(ax1, pts(:, 1), pts(:, 2), pts(:, 3), 'ko', 'MarkerSize', 3, ...
        'MarkerFaceColor', 'k');
end
xlabel(ax1, 'X (m, forward)'); ylabel(ax1, 'Y (m, lateral)');
zlabel(ax1, 'Z (m, up)');
title(ax1, 'Racket head trace (phase-coloured) + arm snapshots');
view(ax1, 35, 18);

% ---- Panel 2: racket speed vs time --------------------------------------
ax2 = subplot(2, 2, 2);
hold(ax2, 'on'); grid(ax2, 'on');
% Phase shading
y_lim = [0, max(frames.racket_speed_mps) * 1.10 + eps];
phase_t = unique([frames.phase_t(:); t(end)]);
for p = 1:numel(phase_t) - 1
    idx = find(frames.phase_id, 1);  % unused, just to keep symmetry
    p0 = phase_t(p);
    p1 = phase_t(p + 1);
    c  = phase_colors(min(p, size(phase_colors, 1)), :);
    patch(ax2, [p0 p1 p1 p0], [y_lim(1) y_lim(1) y_lim(2) y_lim(2)], c, ...
        'FaceAlpha', 0.10, 'EdgeColor', 'none');
end
plot(ax2, t, frames.racket_speed_mps, 'k-', 'LineWidth', 2);
[v_peak, k_peak] = max(frames.racket_speed_mps);
plot(ax2, t(k_peak), v_peak, 'ro', 'MarkerSize', 8, 'MarkerFaceColor', 'r');
text(ax2, t(k_peak), v_peak, sprintf('  peak = %.2f m/s @ t = %.3f s', v_peak, t(k_peak)));
ylim(ax2, y_lim);
xlabel(ax2, 'Time (s)'); ylabel(ax2, 'Racket head speed (m/s)');
title(ax2, 'Racket head speed vs time');

% ---- Panel 3: joint angles ----------------------------------------------
ax3 = subplot(2, 2, 3);
plot(ax3, t, rad2deg(frames.q), 'LineWidth', 1.8);
grid(ax3, 'on');
legend(ax3, {'q1 sh-pitch', 'q2 sh-yaw', 'q3 elbow', 'q4 pron', 'q5 wrist'}, ...
    'Location', 'best');
xlabel(ax3, 'Time (s)'); ylabel(ax3, 'Joint angle (deg)');
title(ax3, 'Joint angles vs time');

% ---- Panel 4: ball trajectory pre/post impact ---------------------------
ax4 = subplot(2, 2, 4);
hold(ax4, 'on'); grid(ax4, 'on'); axis(ax4, 'equal');
plot3(ax4, ball_pre(:, 1), ball_pre(:, 2), ball_pre(:, 3), 'b-', 'LineWidth', 2);
plot3(ax4, ball_post(:, 1), ball_post(:, 2), ball_post(:, 3), 'r-', 'LineWidth', 2);
plot3(ax4, ball_pre(1, 1), ball_pre(1, 2), ball_pre(1, 3), 'go', 'MarkerSize', 8, 'MarkerFaceColor', 'g');
plot3(ax4, ball_pre(end, 1), ball_pre(end, 2), ball_pre(end, 3), 'ko', 'MarkerSize', 8, 'MarkerFaceColor', 'k');
xlabel(ax4, 'X (m)'); ylabel(ax4, 'Y (m)'); zlabel(ax4, 'Z (m)');
legend(ax4, {'pre-impact', 'post-impact', 'spawn', 'impact'}, 'Location', 'best');
title(ax4, 'Ball trajectory (before/after impact)');
view(ax4, 35, 18);

sgtitle('Two-link arm 3D forward swing (kinematic min-jerk, RHS Z-up)');

if ~isempty(savepath)
    try
        exportgraphics(fig, savepath, 'Resolution', 150);
    catch
        % Pre-R2020a fallback
        saveas(fig, savepath);
    end
end
end
