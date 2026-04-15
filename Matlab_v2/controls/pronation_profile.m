function phi = pronation_profile(t, params)
%PRONATION_PROFILE Kinematic pronation proxy phi(t) (rad), Option A (distal orientation).
if ~isfield(params, 'pronation')
    phi = 0;
    return;
end
if ~isfield(params.pronation, 'enable') || ~params.pronation.enable
    phi = 0;
    return;
end
pr = params.pronation;
mag = pr.magnitude_rad;
t0 = pr.onset_s;
T = max(pr.rise_s, eps);
u = (t - t0) / T;
u = max(0, min(1, u));
s = u.^2 .* (3 - 2 * u);
phi = mag * s;
end
