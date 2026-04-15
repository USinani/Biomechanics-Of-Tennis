function export_metrics_json(filepath, metrics)
%EXPORT_METRICS_JSON Scalar summary metrics (vectors omitted).
m = struct();
fn = fieldnames(metrics);
for i = 1:numel(fn)
    v = metrics.(fn{i});
    if isnumeric(v) && isscalar(v)
        m.(fn{i}) = double(v);
    elseif isnumeric(v) && numel(v) > 1
        continue;
    elseif ischar(v)
        m.(fn{i}) = char(v);
    elseif isstruct(v)
        continue;
    end
end
txt = jsonencode(m);
fid = fopen(filepath, 'w');
if fid < 0
    error('export_metrics_json:io', 'Could not write %s', filepath);
end
fprintf(fid, '%s', txt);
fclose(fid);
end
