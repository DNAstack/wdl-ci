version 1.0

# Validate input yaml files
# Input type: YAML/YML

task check_yaml {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		if ! yamllint ~{validated_output}; then
			err "Validated YAML: [~{basename(validated_output)}] is not valid; check format"
			exit 1
		else
			if ! yamllint ~{current_run_output}; then
				err "Current run YAML: [~{basename(current_run_output)}] is not valid"
				exit 1
			else
				echo "Current run YAML: [~{basename(current_run_output)}] is valid"
			fi
		fi
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
