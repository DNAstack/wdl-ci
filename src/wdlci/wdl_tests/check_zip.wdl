version 1.0

# Check integrity of ZIP file
# Input type: ZIP file

task check_zip {
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

		if ! zip -T ~{validated_output}; then
			err "Validated file: [~{basename(validated_output)}] did not pass zip check"
			exit 1
		else
			if ! zip -T ~{current_run_output}; then
				err "Current run file: [~{basename(current_run_output)}] did not pass zip check"
				exit 1
			else
				echo "Current run file: [~{basename(current_run_output)}] passed zip check"
			fi
		fi
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.1.0"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
