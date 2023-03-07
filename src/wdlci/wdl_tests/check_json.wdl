version 1.0

# Validate input json files
# Input type: JSON

task check_json {
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

		# shellcheck disable=SC2002
		if ! cat ~{validated_output} | json_pp; then
			err "Validated JSON is not valid; check schema"
			exit 1
		else
			if ! cat ~{current_run_output}| json_pp; then
				err "Current JSON file is not valid"
				exit 1
			else
				echo "JSON file is valid"
			fi
		fi
	>>>

	output {
		Int rc = read_int("rc")
	}

	runtime {
		docker: "jakubstas/pretty-curl:latest"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
