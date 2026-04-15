function phid = pronation_profile_derivative(t, params)
%PRONATION_PROFILE_DERIVATIVE Time derivative of pronation_profile (rad/s).
if ~isfield(params, 'pronation')
    phid = 0;
    return;
end
if ~isfield(params.pronation, 'enable') || ~params.pronation.enable
    phid = 0;
    return;
end
pr = params.pronation;
mag = pr.magnitude_rad;
t0 = pr.onset_s;
T = max(pr.rise_s, eps);
if t <= t0 || t >= t0 + T
    phid = 0;
    return;
end
u = (t - t0) / T;
phid = mag * 6 * u * (1 - u) / T;
end
