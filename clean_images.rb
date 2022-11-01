images = Dir["docs/img/*"]

for image in images
    basename = File.basename(image)
    puts "ag -c '#{basename}'"
    system "ag -c '#{basename}'"
    if $?.exitstatus != 0
        system "rm #{image}"
        puts "#{image} unused"
    end
end