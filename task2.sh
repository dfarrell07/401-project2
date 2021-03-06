#!/usr/bin/env bash
# Author: Daniel Farrell
# Public Domain
# Runs task2 of the spec using Go-Back-N and graphs the results

TIMEFORMAT=%R

n=64
p=.05
rand_size=1000000
infile=infile
outfile=outfile
shost=152.14.104.45
sport=7735
results=data_gbn2
repeats=20
mss_ceiling=1000
mss_steps=100

# Build file to transfer
echo SCRIPT: Building file to transfer
echo "$(dd if=/dev/urandom bs=1 count=$rand_size)" > $infile

# Add columns to result file
echo "mss,avg_delay" > $results

# Update server's code
echo SCRIPT: Updating remote server code
scp server.py adminuser@$shost:/home/adminuser/p2/

mss=100
repeats_done=0
delay_sum=0
while [ $mss -le $mss_ceiling ]
do
    while [ $repeats_done -lt $repeats ]
    do
        # Kill any running server process
        ssh adminuser@$shost "pkill python"

        # Start server
        echo SCRIPT: Starting remote server with sport:$sport outfile:$outfile p:$p n:$n
        ssh adminuser@$shost "python /home/adminuser/p2/server.py $sport $outfile $p $n > slog &" &

        sleep 2

        # Start client
        echo SCRIPT: Starting client with host:$shost port:$sport n:$n mss:$mss
        delay=$(time (python client.py $shost $sport $infile $n $mss >/dev/null 2>&1) 2>&1)

        # Report run result
        echo "SCRIPT: (mss,delay) is ($mss,$delay)"

        # Update vars
        delay_sum=$(echo "scale=3;$delay_sum+$delay" | bc)
        let repeats_done=$repeats_done+1
    done
    # Get average delay
    avg_delay=$(echo "scale=3;$delay_sum/$repeats_done" | bc)

    echo "SCRIPT: Average (mss,delay_sum) : ($mss,$delay_sum) is $avg_delay"

    # Write results to file
    echo "$mss,$avg_delay" >> $results

    # Update vars
    let mss=$mss+$mss_steps
    repeats_done=0
    delay_sum=0
done

# Kill any running server process
ssh adminuser@$shost "pkill python"

# Build R script that graphs results
echo "gbnd2 <- read.table(\"./data_gbn2\", header=T, sep=\",\")
max_delay <- max(gbnd2\$avg_delay)
plot(x=gbnd2\$mss, y=gbnd2\$avg_delay, ylim=c(min(gbnd2\$avg_delay),1.1*max(gbnd2\$avg_delay)), col='blue', type=\"o\", main='Task 2 - Go-Back-N ARQ', ylab='Delay (Seconds)', xlab='Maximum Segment Size MSS')
abline(lm(gbnd2\$avg_delay~gbnd2\$mss))
box()
" > Rscript_gbn2

# Execute R script
R CMD BATCH ./Rscript_gbn2
