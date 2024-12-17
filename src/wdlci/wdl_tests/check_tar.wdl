version 1.0

# Check integrity of uncompressed tar file
# Input type: uncompressed tar file

task check_tar {
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

		if ! tar tf ~{validated_output} > /dev/null; then
			err "Validated file: [~{basename(validated_output)}] did not pass tar check"
			exit 1
		else
			if ! tar tf ~{current_run_output} > /dev/null; then
				err "Current run file: [~{basename(current_run_output)}] did not pass tar check"
				exit 1
			else
				echo "Current run file: [~{basename(current_run_output)}] passed tar check"
				if ! diff <(tar tf ~{current_run_output} | sort) <(tar tf ~{validated_output} | sort); then
					current_run_output_contents=$(tar tf ~{current_run_output} | sort | tr '\n' ' ' | sed 's/ *$//')
					validated_output_contents=$(tar tf ~{validated_output} | sort | tr '\n' ' ' | sed 's/ *$//')
					err "Current run file: [~{basename(current_run_output)}] and validated file: [~{basename(validated_output)}] do not have the same contents:
						Expected output: [${validated_output_contents}]
						Current run output: [${current_run_output_contents}]"
					exit 1
				else
					echo "Current run file: [~{basename(current_run_output)}] and validated file: [~{basename(validated_output)}] have the same contents"
				fi
			fi
		fi
	>>>

	output {
	}

	runtime {
		docker: "ubuntu:xenial"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
