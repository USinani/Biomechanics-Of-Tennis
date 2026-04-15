function u = control_profile(t, params)
%CONTROL_PROFILE Open-loop joint torques u = [tau_shoulder; tau_elbow] (N*m) at time t.
c = params.control;
ty = lower(char(c.type));
if strcmp(ty, 'none')
    u = [0; 0];
elseif strcmp(ty, 'sine')
    tau0 = c.tau_amp * sin(2 * pi * c.tau_f_hz * t);
    ph = deg2rad(c.tau_phase_deg);
    tau1 = c.tau_amp * sin(2 * pi * c.tau_f_hz * t + ph);
    u = [tau0; tau1];
elseif strcmp(ty, 'step')
    u = torque_profile_step(t, params);
elseif strcmp(ty, 'timedelay')
    u = torque_profile_timedelay(t, params);
elseif strcmp(ty, 'piecewise')
    u = torque_profile_piecewise(t, params);
else
    error('control_profile:type', 'Unknown control.type: %s', char(c.type));
end
u = u(:);
if numel(u) ~= 2
    error('control_profile:dim', 'Torque vector must be 2x1');
end
end
