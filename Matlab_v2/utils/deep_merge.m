function out = deep_merge(base, override)
%DEEP_MERGE Recursively merge struct override into base (override wins).
out = base;
if nargin < 2 || isempty(override)
    return;
end
if ~isstruct(override)
    error('deep_merge:override', 'override must be a struct');
end
f = fieldnames(override);
for i = 1:numel(f)
    name = f{i};
    if isfield(out, name) && isstruct(out.(name)) && isstruct(override.(name))
        out.(name) = deep_merge(out.(name), override.(name));
    else
        out.(name) = override.(name);
    end
end
end
