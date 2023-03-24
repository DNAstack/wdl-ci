version 1.0

# Validate input bigWig files
# Input type: Array of bigWig files

task bigwig_validator_array {
	input {
		Array[File] current_run_output
		Array[File] validated_output
	}

	Int disk_size = ceil((size(current_run_output[0], "GB") * length(current_run_output)) + (size(validated_output[0], "GB") * length(validated_output)) + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		validated_dir_path=$(dirname ~{validated_output[0]})
		current_dir_path=$(dirname ~{current_run_output[0]})

		# Select bigWig files only; -regex works for full path only
		find "$validated_dir_path" -name '*.bw' > validated_bw_list.txt
		find "$current_dir_path" -name '*.bw' > current_bw_list.txt

		while read -r file || [[ -n "$file" ]]; do
			if ! (python3.9 -c "import pyBigWig; bw = pyBigWig.open('$file'); bw.isBigWig();"); then
				err "Validated bigWig file: [$(basename "$file")] is invalid"
				exit 1
			fi
		done < validated_bw_list.txt

		while read -r file || [[ -n "$file" ]]; do
			if (python3.9 -c "import pyBigWig; bw = pyBigWig.open('$file'); bw.isBigWig();"); then
				echo "Current run bigWig file: [$(basename "$file")] is valid"
			else
				err "Current run bigWig file: [$(basename "$file")] is invalid"
				exit 1
			fi
		done < current_bw_list.txt
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.0.1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
