function u = torque_profile_timedelay(t, params)
%TORQUE_PROFILE_TIMEDELAY Sinusoidal bursts with separate joint onset times.
c = params.control;
as = c.shoulder_tau_amp;
ae = c.elbow_tau_amp;
if isempty(as)
    as = c.tau_amp;
end
if isempty(ae)
    ae = c.tau_amp;
end
f = c.tau_f_hz;
ph = deg2rad(c.tau_phase_deg);
ts = max(0, t - c.shoulder_onset);
te = max(0, t - c.elbow_onset);
en_s = double(t >= c.shoulder_onset);
en_e = double(t >= c.elbow_onset);
tau0 = as * sin(2 * pi * f * ts) * en_s;
tau1 = ae * sin(2 * pi * f * te + ph) * en_e;
u = [tau0; tau1];
end
